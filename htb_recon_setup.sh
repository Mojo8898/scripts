#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 <machine_name> <ip_address> <vpn_file> [-s]"
    exit 1
}

# Check if the correct number of arguments is provided
if [ "$#" -lt 3 ]; then
    usage
fi

session=$1
ip=$2
vpn=$3
scan_flag=0

# Check for '-s' argument
if [ "$#" -eq 4 ] && [ "$4" == "-s" ]; then
    scan_flag=1
fi

# Create directory and change to it
mkdir -p /home/kali/htb/machines/$session/nmap && cd /home/kali/htb/machines/$session

# Start tmux session
tmux new-session -d -s $session
tmux set-environment -t $session IP "$ip"
tmux set-environment -t $session SESSION "$session"
tmux send-keys -t $session:0 "clear" C-m

# Connect to VPN
tmux rename-window -t $session:0 "openvpn"
tmux send-keys -t $session:0 "sudo openvpn $vpn" C-m

# Create new window for IP
tmux new-window -t $session -n $ip

# Verify connection
tmux send-keys -t $session:1 "clear" C-m
tmux send-keys -t $session:1 "echo 'Waiting on connection to VPN/host...' && until ping -c1 $ip > /dev/null 2>&1; do sleep .5; done" C-m

# Run nmap scans using the separate script if scan_flag is set
if [ "$scan_flag" -eq 1 ]; then
    tmux send-keys -t $session:1 "clear" C-m
    tmux send-keys -t $session:1 "/home/kali/scripts/scan_machine.sh $ip $session" C-m
fi

tmux attach -t $session

