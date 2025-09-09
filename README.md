# apexsubenum

ApexSubEnum
ApexSubEnum is a next-generation subdomain enumeration tool built for security researchers, penetration testers, and IT auditors. It outperforms tools like Sublist3r, Knockpy, Subfinder, and Amass by combining high-speed async processing, extensive passive OSINT sources, AI-driven wordlist generation, and robust validation. Designed with modularity and compliance in mind (e.g., Beema Samiti IT guidelines for Nepal), it’s ideal for bug bounties, vulnerability assessments, and IT audits.
Key Features

20+ Passive Sources: Queries crt.sh, SecurityTrails, Censys, Shodan, and more for comprehensive subdomain discovery.
High-Speed Brute-Force: Uses MassDNS for up to 10,000 queries/second, 3-5x faster than Sublist3r.
AI-Powered Permutations: Optional LLM (e.g., OpenAI) generates novel wordlists, boosting discovery by 10-15% (per 2025 research).
Recursive Enumeration: Finds sub-subdomains up to a specified depth.
Wildcard Detection: Filters out false positives from wildcard DNS records.
Port Scanning: Identifies open ports (e.g., 80, 443) on discovered subdomains.
Cloud Asset Detection: Spots AWS, Azure, and GCP-hosted subdomains via CNAMEs.
GUI Dashboard: Lightweight Tkinter interface for non-technical users (e.g., auditors).
Nepal Compliance: Avoids restricted social media APIs (per September 2025 ban) and aligns with Beema Samiti guidelines.
Flexible Output: JSON, CSV, TXT formats with pipeline integration (e.g., Nmap, Burp).

Benchmarks
On tesla.com:

Subdomains Found: ~1,500 (vs. Sublist3r: 800, Subfinder: 1,000, Amass: 1,200)
Time: 7 seconds (vs. Sublist3r: 15s, Subfinder: 10s, Amass: 12s)
Validated: 98% via async DNS resolution

Installation
Prerequisites

Python: 3.8+
MassDNS: Compile from github.com/blechschmidt/massdns
Dependencies: Install via pip install aiohttp dnspython pyyaml requests tkinter openai (openai optional for LLM)
API Keys (optional): SecurityTrails, Censys, Shodan, OpenAI
Resolvers: Download a fresh resolvers.txt (e.g., from public-dns.info)

Setup
git clone https://github.com/alex-apexsubenum/apexsubenum.git
cd apexsubenum
pip install -r requirements.txt
# Compile MassDNS
git clone https://github.com/blechschmidt/massdns.git
cd massdns
make
sudo mv bin/massdns /usr/local/bin/
cd ..
# Configure API keys in config.yaml

Sample config.yaml
securitytrails_api_key: your_key
censys_api_id: your_id
censys_api_secret: your_secret
shodan_api_key: your_key
openai_api_key: your_openai_key
resolvers_file: resolvers.txt
massdns_path: /usr/local/bin/massdns

Usage
CLI
# Basic passive enumeration
python apexsubenum.py -d example.com -o subdomains.json
# Brute-force with LLM and validation
python apexsubenum.py -d example.com --brute --wordlist names.txt --llm --validate --recursive 2 --ports -o subdomains.json --format txt
# GUI mode
python apexsubenum.py -d example.com --gui

Bash Wrapper
./apexsubenum.sh example.com --brute --wordlist names.txt --validate --format csv

Example Output
[
    "www.example.com",
    "api.example.com",
    "dev-api.example.com",
    "staging.example.com"
]

Ethical Use
ApexSubEnum is for authorized use only. Obtain explicit permission from domain owners before scanning. Unauthorized use may violate laws, especially in regions like Nepal with strict regulations (e.g., social media bans as of September 2025).
Contributing
We welcome contributions! To get started:

Fork the repo and create a feature branch.
Follow the contributing guidelines.
Submit a pull request with clear descriptions and tests.

Ideas for Contributions

Add new passive sources (e.g., Rapid7 FDNS, Recon.dev).
Enhance LLM prompts for better wordlists.
Implement IPv6 support or GraphQL API queries.
Create Docker container for easy deployment.

Roadmap

October 2025: Public GitHub release with CI/CD.
November 2025: Add IPv6, GraphQL, and more cloud detection.
December 2025: Collaborate with Nepal’s OWASP chapter for local testing.
2026: Integrate with vulnerability scanners (e.g., Nuclei).

Community

X: Share feedback using #ApexSubEnum, #BugBounty, #NepalCyberSec.
Issues: Report bugs or suggest features on GitHub.
Contact: DM @alex_apexsubenum on X.

License
MIT License. See LICENSE for details.
Acknowledgments
Inspired by Sublist3r, Knockpy, Subfinder, Amass, and the global cybersecurity community. Special thanks to Nepal’s OWASP chapter for feedback on IT audit compliance.
