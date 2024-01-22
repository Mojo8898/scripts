#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <ip_address> <session> <port> <protocol>"
    exit 1
fi

ip=$1
session=$2
port=$3
protocol=$4

handle_redirect() {
    local url="http://$ip"
    if [ "$port" == "443" ]; then
        local url="https://$ip"
    fi

    local response=$(curl -Ls -o /dev/null -w "%{http_code} %{url_effective}" "$url")

    local http_code=$(echo "$response" | awk '{print $1}')
    local effective_url=$(echo "$response" | awk '{print $2}')

    if [[ "$http_code" == "301" || "$http_code" == "302" ]]; then
        local domain=$(echo "$effective_url" | awk -F/ '{print $3}')
        echo "$ip $domain" | sudo tee -a /etc/hosts >/dev/null
    fi
    echo "$effective_url"
}

# echo "Debug: $port/$protocol" | tee -a "$HOME/htb/machines/$session/commands.txt" >/dev/null

# Main logic to handle ports and protocols
if [ "$protocol" == "tcp" ]; then
    if [[ "$port" == "80" || "$port" == "443" ]]; then
        url=$(handle_redirect)
        if [ -n "$url" ]; then
            :
            # firefox "$url" &> /dev/null &
            # burpsuite &> /dev/null &
            # echo 'http!' | tee -a "$HOME/htb/machines/$session/commands.txt" >/dev/null
        fi
    fi
else
    : # To-do: handle UDP
fi
