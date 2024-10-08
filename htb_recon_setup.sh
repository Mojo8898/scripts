#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <machine_name> <ip_address> <vpn_file>"
    exit 1
fi

session=$1
ip=$2
vpn=$3

# Create working environment
mkdir -p "$HOME/htb/machines/$session"
if [ $? -ne 0 ]; then
    echo "Failed to create directory for session $session"
    exit 1
fi
cd "$HOME/htb/machines/$session"

# Start tmux session
tmux new-session -d -s $session
tmux set-environment -t $session IP "$ip"

# Connect to VPN
tmux send-keys -t $session:0 "clear" C-m
tmux rename-window -t $session:0 "openvpn"
tmux send-keys -t $session:0 "sudo openvpn $vpn" C-m

# Create new window to work in
tmux new-window -t $session -n $ip
tmux send-keys -t $session:1 "clear" C-m
tmux send-keys -t $session:1 "sleep .2" C-m
tmux send-keys -t $session:1 "clear" C-m

# Call the scan_machine.sh script
# tmux send-keys -t $session:1 "echo 'Waiting on connection to VPN/host...'"
tmux send-keys -t $session:1 "until ping -c1 -W 0.5 $ip >/dev/null 2>&1; do :; done" C-m
tmux send-keys -t $session:1 "clear" C-m
tmux send-keys -t $session:1 "$HOME/scripts/scan_machine.sh $ip" C-m

# Create a new pane to dynamically view recommended commands based on nmap output
tmux split-window -h -t $session:1
tmux send-keys -t $session:1 "clear" C-m
tmux send-keys -t $session:1 "sleep .2" C-m
tmux send-keys -t $session:1 "clear" C-m

# Attach to the tmux session
tmux attach -t $session