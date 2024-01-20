#!/bin/bash

# Check for correct number of arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <ip_address> <outfile_name>"
    exit 1
fi

ip=$1
outfile_name=$2

# Directory for nmap results
mkdir -p nmap/$outfile_name

# UDP scan
sudo nmap -Pn -sU --top-ports=200 -oN nmap/$outfile_name/udp.nmap -v $ip
echo '<=================================================================================>'

