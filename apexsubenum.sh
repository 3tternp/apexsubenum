#!/bin/bash

# Check dependencies
command -v python3 >/dev/null 2>&1 || { echo "Python3 required. Install it!"; exit 1; }
command -v massdns >/dev/null 2>&1 || { echo "MassDNS required. Compile from github.com/blechschmidt/massdns"; exit 1; }
pip show aiohttp >/dev/null 2>&1 || pip install aiohttp
pip show dnspython >/dev/null 2>&1 || pip install dnspython
pip show pyyaml >/dev/null 2>&1 || pip install pyyaml
pip show requests >/dev/null 2>&1 || pip install requests
pip show openai >/dev/null 2>&1 || echo "OpenAI optional for LLM. Install with: pip install openai"

# Usage
if [ $# -lt 1 ]; then
    echo "Usage: $0 <domain> [options]"
    echo "Options: --brute --wordlist <file> --validate --llm --output <file> --format <json|csv|txt> --recursive <depth> --ports --gui"
    exit 1
fi

DOMAIN=$1
shift
OPTIONS="$@"

# Run Python tool
python3 apexsubenum.py -d "$DOMAIN" $OPTIONS

# Post-process (e.g., chain to Nmap)
echo "Enumeration complete for $DOMAIN. Run 'nmap -iL subdomains.txt' for further scanning."
