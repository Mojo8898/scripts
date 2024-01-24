#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <ip_address>"
    exit 1
fi

ip=$1

# Function to check if scan was completed (file exists and has more than one line)
was_scan_completed() {
    local file=$1
    [ -s "$file" ] && [ "$(wc -l < "$file")" -gt 1 ]
}

# Verify connection
echo 'Waiting on connection to VPN/host...' && until ping -c1 -W 0.5 $ip >/dev/null 2>&1; do :; done

# TCP scans
full_tcp_file="nmap/full_tcp.nmap"
targeted_tcp_file="nmap/targeted_tcp.nmap"

if ! was_scan_completed "$targeted_tcp_file"; then
    sudo nmap -Pn -p- --min-rate=1000 -oN "$full_tcp_file" -v $ip
    echo -e '\n  <===============================================================================================================>  \n'

    # Extract open ports for targeted scan
    ports=$(cat "$full_tcp_file" | grep '^[0-9]' | awk '/open/{print $1}' | cut -d '/' -f 1 | paste -sd,)
    echo "$ports" > "nmap/open_tcp.txt"

    # Targeted TCP scan
    if [ -n "$ports" ]; then
        sudo nmap -Pn -sC -sV -oN "$targeted_tcp_file" -p $ports $ip
    else
        echo "Full TCP was not completed; skipping targeted TCP scan."
    fi
else
    cat $targeted_tcp_file
fi
echo -e '\n  <===============================================================================================================>  \n'

# UDP scan
udp_file="nmap/udp.nmap"

if ! was_scan_completed "$udp_file"; then
    sudo nmap -Pn -sU --top-ports=200 -oN "$udp_file" -v $ip
else
    cat $udp_file
fi
