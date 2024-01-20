#!/bin/bash

ip=$1
session=$2

handle_redirect() {
    local url=$1
    local response=$(curl -Ls -o /dev/null -w "%{http_code} %{url_effective}" "$url")

    local http_code=$(echo "$response" | awk '{print $1}')
    local effective_url=$(echo "$response" | awk '{print $2}')

    if [[ "$http_code" == "302" || "$http_code" == "301" ]]; then
        local domain=$(echo "$effective_url" | awk -F/ '{print $3}')
        echo "$ip $domain" | sudo tee -a /etc/hosts
        echo "$effective_url"
    else
        echo "$url"
    fi
}

launch_applications() {
    local outfile_path="/home/kali/htb/machines/$session/nmap/$session/openports.txt"
    if [ -f "$outfile_path" ]; then
        local url_to_open=""

        if grep -q '80' "$outfile_path"; then
            url_to_open=$(handle_redirect "http://$ip")
        elif grep -q '443' "$outfile_path"; then
            url_to_open=$(handle_redirect "https://$ip")
        fi

        if [ -n "$url_to_open" ]; then
            # Launch Firefox
            firefox "$url_to_open" &> /dev/null &

            # Launch Burp Suite
            burpsuite &> /dev/null &
        fi
    fi
}

launch_applications
