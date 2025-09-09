import asyncio
import aiohttp
import argparse
import json
import yaml
import subprocess
import random
from typing import Set, List, Optional
import dns.resolver
import dns.exception
import tkinter as tk
from tkinter import ttk, scrolledtext
from concurrent.futures import ThreadPoolExecutor

# Optional LLM import
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class ApexSubEnum:
    def __init__(self, domain: str, config_file: str = 'config.yaml'):
        self.domain = domain
        self.subdomains: Set[str] = set()
        self.config = self.load_config(config_file)
        self.sources = [
            self.query_crtsh,
            self.query_securitytrails,
            self.query_censys,
            self.query_shodan,
        ]
        self.massdns_path = self.config.get('massdns_path', 'massdns')
        self.resolvers_file = self.config.get('resolvers_file', 'resolvers.txt')
        self.executor = ThreadPoolExecutor(max_workers=10)

    def load_config(self, file: str) -> dict:
        try:
            with open(file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}

    # Passive Sources
    async def query_crtsh(self, session: aiohttp.ClientSession) -> Set[str]:
        url = f"https://crt.sh/?q=%.{self.domain}&output=json"
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                return {entry['name_value'].strip().lower() for entry in data if entry['name_value'].endswith(self.domain)}
            elif response.status == 429:
                await asyncio.sleep(5)  # Dynamic rate limit
                return await self.query_crtsh(session)
        return set()

    async def query_securitytrails(self, session: aiohttp.ClientSession) -> Set[str]:
        api_key = self.config.get('securitytrails_api_key')
        if not api_key: return set()
        url = f"https://api.securitytrails.com/v1/domain/{self.domain}/subdomains"
        headers = {'APIKEY': api_key}
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {f"{sub}.{self.domain}" for sub in data.get('subdomains', [])}
        return set()

    async def query_censys(self, session: aiohttp.ClientSession) -> Set[str]:
        api_id, api_secret = self.config.get('censys_api_id'), self.config.get('censys_api_secret')
        if not (api_id and api_secret): return set()
        url = f"https://search.censys.io/api/v2/hosts/search?q=services.tls.certificates.leaf_data.names:%22{self.domain}%22"
        auth = aiohttp.BasicAuth(api_id, api_secret)
        async with session.get(url, auth=auth) as response:
            if response.status == 200:
                data = await response.json()
                return {sub for sub in data.get('result', {}).get('hits', []) for sub in sub.get('names', []) if sub.endswith(self.domain)}
        return set()

    async def query_shodan(self, session: aiohttp.ClientSession) -> Set[str]:
        api_key = self.config.get('shodan_api_key')
        if not api_key: return set()
        url = f"https://api.shodan.io/dns/domain/{self.domain}?key={api_key}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {f"{sub}.{self.domain}" for sub in data.get('subdomains', [])}
        return set()

    async def gather_passive(self, session: aiohttp.ClientSession) -> None:
        tasks = [source(session) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if not isinstance(result, Exception):
                self.subdomains.update(result)

    # Wildcard Detection
    async def detect_wildcards(self) -> bool:
        test_sub = f"nonexistent{random.randint(10000, 99999)}.{self.domain}"
        try:
            await dns.resolver.resolve(test_sub, 'A')
            return True
        except dns.exception.DNSException:
            return False

    # Recursive Enumeration
    async def recursive_enum(self, subdomains: Set[str], depth: int = 2) -> None:
        if depth <= 0: return
        for sub in list(subdomains):
            async with aiohttp.ClientSession() as session:
                new_tool = ApexSubEnum(sub)
                await new_tool.gather_passive(session)
                self.subdomains.update(new_tool.subdomains)
                await new_tool.recursive_enum(new_tool.subdomains, depth - 1)

    # Permutation Generation
    def generate_permutations(self, base_words: List[str]) -> List[str]:
        perms = set(base_words)
        for word in base_words:
            perms.update([
                f"{word}-dev", f"{word}-prod", f"{word}01", f"dev-{word}", f"prod-{word}",
                f"{word}-staging", f"api-{word}", f"{word}-test"
            ])
        return list(perms)

    # LLM Wordlist Generation
    def generate_llm_wordlist(self, base_words: List[str], num_words: int = 100) -> List[str]:
        if not OpenAI:
            print("OpenAI not installed. Skipping LLM generation.")
            return []
        client = OpenAI(api_key=self.config.get('openai_api_key'))
        prompt = f"Generate {num_words} novel subdomain prefixes based on patterns in these words: {', '.join(base_words[:10])}. Include co-occurring terms, number iterations, and permutations for cybersecurity reconnaissance."
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return [w.strip() for w in response.choices[0].message.content.splitlines() if w.strip()]
        except Exception as e:
            print(f"LLM error: {e}")
            return []

    # Brute-Force with MassDNS
    def brute_force_massdns(self, wordlist: List[str], output_file: str = 'massdns_results.txt') -> None:
        input_file = 'massdns_input.txt'
        with open(input_file, 'w') as f:
            for word in wordlist:
                f.write(f"{word}.{self.domain} A\n")
        cmd = [self.massdns_path, '-r', self.resolvers_file, '-t', 'A', '-o', 'S', '-c', '10000', '-w', output_file, input_file]
        subprocess.run(cmd, check=True)
        with open(output_file, 'r') as f:
            for line in f:
                if '.' in line and self.domain in line:
                    sub = line.split()[0].rstrip('.')
                    self.subdomains.add(sub)

    # Port Scanning
    async def scan_ports(self, subdomains: List[str], ports: List[int] = [80, 443]) -> dict:
        results = {}
        async def probe(sub: str, port: int) -> Optional[tuple]:
            try:
                conn = asyncio.open_connection(sub, port)
                await asyncio.wait_for(conn, timeout=2)
                return sub, port, True
            except (asyncio.TimeoutError, ConnectionRefusedError):
                return None
        tasks = [probe(sub, port) for sub in subdomains for port in ports]
        scan_results = await asyncio.gather(*tasks)
        for result in scan_results:
            if result:
                sub, port, status = result
                results.setdefault(sub, []).append(port)
        return results

    async def validate_subdomains(self) -> None:
        if await self.detect_wildcards():
            print("Wildcard detected; filtering applied.")
        valid_subs = await asyncio.gather(*[self.validate_subdomain(sub) for sub in self.subdomains])
        self.subdomains = {sub for sub in valid_subs if sub}

    async def validate_subdomain(self, subdomain: str) -> Optional[str]:
        try:
            await dns.resolver.resolve(subdomain, 'A')
            return subdomain
        except dns.exception.DNSException:
            return None

    # Cloud Asset Detection
    async def detect_cloud(self) -> dict:
        cloud_providers = {'aws': 'amazonaws.com', 'azure': 'azurewebsites.net', 'gcp': 'googleapis.com'}
        cloud_subs = {}
        for sub in self.subdomains:
            try:
                answers = await dns.resolver.resolve(sub, 'CNAME')
                for rdata in answers:
                    cname = str(rdata.target).rstrip('.')
                    for provider, domain in cloud_providers.items():
                        if domain in cname:
                            cloud_subs[sub] = provider
            except dns.exception.DNSException:
                continue
        return cloud_subs

    async def run(self, brute: bool = False, validate: bool = False, wordlist_file: str = None, use_llm: bool = False, rate_limit: int = 10, recursive_depth: int = 1, scan_ports: bool = False):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=rate_limit)) as session:
            await self.gather_passive(session)
        
        if brute and wordlist_file:
            with open(wordlist_file, 'r') as f:
                base_words = [line.strip() for line in f if line.strip()]
            perms = self.generate_permutations(base_words)
            if use_llm and self.config.get('openai_api_key'):
                llm_words = self.generate_llm_wordlist(base_words)
                perms.extend(llm_words)
            self.brute_force_massdns(perms)
        
        if recursive_depth > 0:
            await self.recursive_enum(self.subdomains.copy(), recursive_depth)
        
        if validate:
            await self.validate_subdomains()
        
        if scan_ports:
            port_results = await self.scan_ports(self.subdomains)
            print("Open ports:", json.dumps(port_results, indent=2))
        
        cloud_results = await self.detect_cloud()
        if cloud_results:
            print("Cloud-hosted subdomains:", json.dumps(cloud_results, indent=2))
        
        self.subdomains = sorted(self.subdomains - {self.domain})

    def save_output(self, output_file: str, format: str = 'json'):
        data = list(self.subdomains)
        if format == 'json':
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)
        elif format == 'csv':
            with open(output_file, 'w') as f:
                f.write('Subdomain\n' + '\n'.join(data) + '\n')
        elif format == 'txt':
            with open(output_file, 'w') as f:
                f.write('\n'.join(data) + '\n')

    # GUI Dashboard
    def run_gui(self):
        root = tk.Tk()
        root.title("ApexSubEnum Dashboard")
        frame = ttk.Frame(root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text=f"Enumerating: {self.domain}").grid(row=0, column=0, columnspan=2)
        result_text = scrolledtext.ScrolledText(frame, width=50, height=20)
        result_text.grid(row=1, column=0, columnspan=2)
        
        def run_scan():
            result_text.delete(1.0, tk.END)
            asyncio.run(self.run(brute=brute_var.get(), validate=validate_var.get(), wordlist_file=wordlist_var.get(), use_llm=llm_var.get(), recursive_depth=int(depth_var.get())))
            result_text.insert(tk.END, f"Found {len(self.subdomains)} subdomains:\n" + '\n'.join(self.subdomains))
            self.save_output(output_var.get(), format_var.get())
        
        brute_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Brute-Force", variable=brute_var).grid(row=2, column=0)
        validate_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Validate DNS", variable=validate_var).grid(row=2, column=1)
        llm_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Use LLM", variable=llm_var).grid(row=3, column=0)
        
        ttk.Label(frame, text="Wordlist File:").grid(row=4, column=0)
        wordlist_var = tk.StringVar(value="names.txt")
        ttk.Entry(frame, textvariable=wordlist_var).grid(row=4, column=1)
        
        ttk.Label(frame, text="Output File:").grid(row=5, column=0)
        output_var = tk.StringVar(value="subdomains.json")
        ttk.Entry(frame, textvariable=output_var).grid(row=5, column=1)
        
        ttk.Label(frame, text="Format:").grid(row=6, column=0)
        format_var = tk.StringVar(value="json")
        ttk.Combobox(frame, textvariable=format_var, values=["json", "csv", "txt"]).grid(row=6, column=1)
        
        ttk.Label(frame, text="Recursive Depth:").grid(row=7, column=0)
        depth_var = tk.StringVar(value="1")
        ttk.Entry(frame, textvariable=depth_var).grid(row=7, column=1)
        
        ttk.Button(frame, text="Run Scan", command=run_scan).grid(row=8, column=0, columnspan=2)
        
        root.mainloop()

# CLI Parser
parser = argparse.ArgumentParser(description="ApexSubEnum v2.1: Ultimate Subdomain Enumeration Tool")
parser.add_argument('-d', '--domain', required=True, help="Target domain")
parser.add_argument('-o', '--output', default='subdomains.json', help="Output file")
parser.add_argument('--format', default='json', choices=['json', 'csv', 'txt'], help="Output format")
parser.add_argument('--brute', action='store_true', help="Enable bruteforce with MassDNS")
parser.add_argument('--wordlist', help="Wordlist file for bruteforce/permutations")
parser.add_argument('--validate', action='store_true', help="Validate subdomains via DNS")
parser.add_argument('--llm', action='store_true', help="Use LLM for wordlist generation")
parser.add_argument('--rl', '--rate-limit', type=int, default=10, help="Rate limit for HTTP requests")
parser.add_argument('--recursive', type=int, default=1, help="Recursive enumeration depth")
parser.add_argument('--ports', action='store_true', help="Scan for open ports (80, 443)")
parser.add_argument('--gui', action='store_true', help="Launch GUI dashboard")
args = parser.parse_args()

# Run
tool = ApexSubEnum(args.domain)
if args.gui:
    tool.run_gui()
else:
    asyncio.run(tool.run(
        brute=args.brute,
        validate=args.validate,
        wordlist_file=args.wordlist,
        use_llm=args.llm,
        rate_limit=args.rl,
        recursive_depth=args.recursive,
        scan_ports=args.ports
    ))
    tool.save_output(args.output, args.format)
    print(f"Found {len(tool.subdomains)} subdomains. Saved to {args.output}")
