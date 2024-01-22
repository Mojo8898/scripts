#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <ip_address> <session>"
    exit 1
fi

ip=$1
session=$2

# Function to check if scan was completed (file exists and has more than one line)
was_scan_completed() {
    local file=$1
    [ -s "$file" ] && [ "$(wc -l < "$file")" -gt 1 ]
}

# Function to check full TCP scan lines and launch tools based on discovered open ports
check_discovered_tcp_line() {
    local line=$1
    if echo "$line" | grep -q 'Discovered open port'; then
        local port=$(echo "$line" | awk '{print $4}' | cut -d'/' -f1)
        local protocol=$(echo "$line" | awk '{print $4}' | cut -d'/' -f2)
        "$HOME/scripts/htb/launch_tools.sh" "$ip" "$session" "$port" "$protocol"
    fi
}

# Function to check scan lines (both TCP and UDP) and launch tools based on open ports
check_targeted_tcp_line() {
    local line=$1
    if echo "$line" | grep -qE '^[0-9]+/tcp'; then
        local port=$(echo "$line" | awk '{print $1}' | cut -d'/' -f1)
        local protocol=$(echo "$line" | awk '{print $1}' | cut -d'/' -f2)
        "$HOME/scripts/htb/launch_tools.sh" "$ip" "$session" "$port" "$protocol"
    fi
}

# Function to check UDP scan lines and launch tools based on open ports
check_udp_line() {
    local line=$1
    if echo "$line" | grep -qE '^[0-9]+/udp'; then
        local port=$(echo "$line" | awk '{print $1}' | cut -d'/' -f1)
        local protocol=$(echo "$line" | awk '{print $1}' | cut -d'/' -f2)
        "$HOME/scripts/htb/launch_tools.sh" "$ip" "$session" "$port" "$protocol"
    fi
}

# Verify connection
echo 'Waiting on connection to VPN/host...' && until ping -c1 -W 0.5 $ip >/dev/null 2>&1; do :; done

# TCP scans
full_tcp_file="nmap/full_tcp.nmap"
targeted_tcp_file="nmap/targeted_tcp.nmap"

if ! was_scan_completed "$targeted_tcp_file"; then
    # Check discovered ports during nmap scan
    sudo nmap -Pn -p- --min-rate=1000 -oN "$full_tcp_file" -v $ip | while read line; do
        echo "$line"
        check_discovered_tcp_line "$line"
    done
    echo -e '\n  <===============================================================================================================>  \n'

    # Extract open ports for targeted scan
    ports=$(cat "$full_tcp_file" | grep '^[0-9]' | awk '/open/{print $1}' | cut -d '/' -f 1 | paste -sd,)
    echo "$ports" > "nmap/open_tcp.txt"

    # Targeted TCP scan
    if [ -n "$ports" ]; then
        sudo nmap -Pn -sC -sV -oN "$targeted_tcp_file" -p $ports $ip | while read line; do
            echo "$line"
            check_targeted_tcp_line "$line"
        done
    else
        echo "Full TCP was not completed; skipping targeted TCP scan."
    fi
else
    while read line; do
        echo "$line"
        check_targeted_tcp_line "$line"
    done < "$targeted_tcp_file"
fi
echo -e '\n  <===============================================================================================================>  \n'

# UDP scan
udp_file="nmap/udp.nmap"

if ! was_scan_completed "$udp_file"; then
    sudo nmap -Pn -sU --top-ports=200 -oN "$udp_file" -v $ip | while read line; do
        echo "$line"
        check_udp_line "$line"
    done
else
    while read line; do
        echo "$line"
        check_udp_line "$line"
    done < "$udp_file"
fi
