#!/bin/bash

# Check for correct number of arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <ip_range> <network_name>"
    exit 1
fi

ip_range=$1
network_name=$2
session=$(basename $(pwd))

mkdir -p nmap

# Discover hosts
sudo nmap -sn -oG nmap/$network_name.txt $ip_range

# Extract the list of hosts
hosts=$(cat nmap/$network_name.txt | grep Up | cut -d ' ' -f 2)

# Run TCP scans for all hosts
echo -e "\nStarting TCP scans...\n"
for host in $hosts; do
    echo -e "\nStarting TCP scan for: $host\n"
    "$HOME/scripts/misc/tcp_scan.sh" "$host" "$session-$host"
done

# Run UDP scans for all hosts
echo -e "\nStarting UDP scans...\n"
for host in $hosts; do
    echo -e "\nStarting UDP scan for: $host\n"
    "$HOME/scripts/misc/udp_scan.sh" "$host" "$session-$host"
done

