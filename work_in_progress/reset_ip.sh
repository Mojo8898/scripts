#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 <session_name> <new_ip_address>"
    exit 1
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    usage
fi

session_name=$1
new_ip=$2

# Update the IP environment variable in the tmux session
tmux set-environment -t $session_name IP "$new_ip"
