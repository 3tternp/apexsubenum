#!/bin/bash

# ────────────────────────────────
# ApexSubEnum v2.1 Banner
# ────────────────────────────────
print_banner() {
cat << "EOF"
     ___                        _____       _                       
    /   |  ____  ____  ___     / ___/____  (_)___  ____ _____  _____
   / /| | / __ \/ __ \/ _ \    \__ \/ __ \/ / __ \/ __ `/ __ \/ ___/
  / ___ |/ /_/ / /_/ /  __/   ___/ / /_/ / / / / / /_/ / / / (__  ) 
 /_/  |_/ .___/ .___/\___/   /____/ .___/_/_/ /_/\__,_/_/ /_/____/  
       /_/   /_/                     /_/                            
              ApexSubEnum v2.1 - Next-Gen Subdomain Enumeration
EOF
}

# Print banner at startup
print_banner

# ────────────────────────────────
# Dependency Check
# ────────────────────────────────
command -v python3 >/dev/null 2>&1 || { echo "[!] Python3 required. Install it!"; exit 1; }
command -v massdns >/dev/null 2>&1 || { echo "[!] MassDNS required. Compile from github.com/blechschmidt/massdns"; exit 1; }

# Python dependencies (auto-install if missing)
pip show aiohttp >/dev/null 2>&1 || pip install aiohttp
pip show dnspython >/dev/null 2>&1 || pip install dnspython
pip show pyyaml >/dev/null 2>&1 || pip install pyyaml
pip show requests >/dev/null 2>&1 || pip install requests
pip show openai >/dev/null 2>&1 || echo "[*] OpenAI optional for LLM. Install with: pip install openai"

# ────────────────────────────────
# Usage Help
# ────────────────────────────────
if [ $# -lt 1 ]; then
    echo "Usage: $0 <domain> [options]"
    echo
    echo "Options:"
    echo "  --brute                  Enable bruteforce with MassDNS"
    echo "  --wordlist <file>        Wordlist file for bruteforce/permutations"
    echo "  --validate               Validate subdomains via DNS"
    echo "  --llm                    Use LLM for wordlist generation"
    echo "  --output <file>          Output file (default: subdomains.json)"
    echo "  --format <json|csv|txt>  Output format"
    echo "  --recursive <depth>      Recursive enumeration depth"
    echo "  --ports                  Scan for open ports (80,443)"
    echo "  --gui                    Launch GUI dashboard"
    echo
    exit 1
fi

# ────────────────────────────────
# Run ApexSubEnum
# ────────────────────────────────
DOMAIN=$1
shift
OPTIONS="$@"

python3 apexsubenum.py -d "$DOMAIN" $OPTIONS

# ────────────────────────────────
# Post-processing Suggestion
# ────────────────────────────────
echo
echo "[+] Enumeration complete for $DOMAIN."
echo "[*] Suggested next step: run 'nmap -iL subdomains.txt' for further scanning."
