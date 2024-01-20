#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <ip_address> <outfile_name>"
    exit 1
fi

ip=$1
outfile_name=$2

# Directory for nmap results
mkdir -p nmap/$outfile_name

# Full TCP scan
sudo nmap -Pn -p- --min-rate=1000 -oN nmap/$outfile_name/allports.nmap -v $ip
echo '<=================================================================================>'

# Extract open ports for targeted scan
ports=$(cat nmap/$outfile_name/allports.nmap | grep '^[0-9]' | awk '/open/{print $1}' | cut -d '/' -f 1 | paste -sd,)
echo "$ports" > nmap/$outfile_name/openports.txt

# Targeted TCP scan
[ -n "$ports" ] && sudo nmap -Pn -sC -sV -oN nmap/$outfile_name/tcp.nmap -p $ports $ip
echo '<=================================================================================>'

# UDP scan
sudo nmap -Pn -sU --top-ports=200 -oN nmap/$outfile_name/udp.nmap -v $ip

