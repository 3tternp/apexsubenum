#!/bin/bash

# ────────────────────────────────
# ApexSubEnum v2.1 Banner (Colorized)
# ────────────────────────────────
print_banner() {
CYAN="\033[1;36m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo -e "${CYAN}"
cat << "EOF"
    ___                        _____       _       
   /   |  ____  ____  _____   / ___/____  (_)___   
  / /| | / __ \/ __ \/ ___/   \__ \/ __ \/ / __ \  
 / ___ |/ /_/ / /_/ (__  )   ___/ / /_/ / / / / /  
/_/  |_|\____/\____/____/   /____/\____/_/_/ /_/   

      █████╗ ██████╗ ███████╗██╗  ██╗███████╗██╗   ██╗███╗   ███╗
     ██╔══██╗██╔══██╗██╔════╝██║  ██║██╔════╝██║   ██║████╗ ████║
     ███████║██████╔╝█████╗  ███████║███████╗██║   ██║██╔████╔██║
     ██╔══██║██╔═══╝ ██╔══╝  ██╔══██║╚════██║██║   ██║██║╚██╔╝██║
     ██║  ██║██║     ███████╗██║  ██║███████║╚██████╔╝██║ ╚═╝ ██║
     ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝     ╚═╝
EOF
echo -e "${YELLOW}              ApexSubEnum v2.1 - Next-Gen Subdomain Enumeration${RESET}\n"
}

# Print banner at startup
print_banner

# ────────────────────────────────
# Colors
# ────────────────────────────────
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

# ────────────────────────────────
# Dependency Check
# ────────────────────────────────
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo -e "${GREEN}[✓] $1 found${RESET}"
    else
        echo -e "${RED}[✗] $1 missing!${RESET} -> $2"
        exit 1
    fi
}

check_python_package() {
    if pip show "$1" >/dev/null 2>&1; then
        echo -e "${GREEN}[✓] Python package $1 installed${RESET}"
    else
        echo -e "${RED}[✗] Python package $1 missing${RESET} -> Installing..."
        pip install "$1"
    fi
}

# Commands
check_command python3 "Install Python3"
check_command massdns "Compile from github.com/blechschmidt/massdns"

# Python packages
check_python_package aiohttp
check_python_package dnspython
check_python_package pyyaml
check_python_package requests

# Optional
if pip show openai >/dev/null 2>&1; then
    echo -e "${GREEN}[✓] Python package openai installed (LLM ready)${RESET}"
else
    echo -e "${YELLOW}[!] OpenAI not installed. Optional for LLM (pip install openai)${RESET}"
fi

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

OUTPUT_FILE="subdomains.json"
if [[ "$OPTIONS" == *"--output"* ]]; then
    OUTPUT_FILE=$(echo "$OPTIONS" | sed -n 's/.*--output \([^ ]*\).*/\1/p')
fi

python3 apexsubenum.py -d "$DOMAIN" $OPTIONS

# ────────────────────────────────
# Print results in GREEN
# ────────────────────────────────
if [ -f "$OUTPUT_FILE" ]; then
    echo
    echo -e "${GREEN}[✓] Enumeration complete for $DOMAIN.${RESET}"
    echo -e "${YELLOW}[*] Results from $OUTPUT_FILE:${RESET}"
    echo -e "${GREEN}"
    cat "$OUTPUT_FILE"
    echo -e "${RESET}"
else
    echo -e "${RED}[✗] No results file ($OUTPUT_FILE) found.${RESET}"
fi

# ────────────────────────────────
# Post-processing Suggestion
# ────────────────────────────────
echo -e "${YELLOW}[*] Suggested next step: run 'nmap -iL subdomains.txt' for further scanning.${RESET}"
