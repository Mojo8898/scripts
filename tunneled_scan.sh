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

# Create nmap directory
mkdir -p "$ip/nmap"
if [ $? -ne 0 ]; then
    echo "Failed to create nmap directory"
    exit 1
fi

# TCP scan
targeted_tcp_file="$ip/nmap/targeted_tcp.nmap"

if ! was_scan_completed "$targeted_tcp_file"; then
    proxychains nmap -Pn -sC -sV --top-ports=200 -oN "$targeted_tcp_file" -v $ip
else
    cat $targeted_tcp_file
fi
echo -e '\n  <===============================================================================================================>\n'
