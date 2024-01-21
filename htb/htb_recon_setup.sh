#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <machine_name> <ip_address> <vpn_file>"
    exit 1
fi

session=$1
ip=$2
vpn=$3

# Create directory and change to it
mkdir -p "$HOME/htb/machines/$session/nmap" && cd "$HOME/htb/machines/$session"

# Start tmux session
tmux new-session -d -s $session
tmux set-environment -t $session IP "$ip"
tmux set-environment -t $session SESSION "$session"

# Connect to VPN
tmux send-keys -t $session:0 "clear" C-m
tmux rename-window -t $session:0 "openvpn"
tmux send-keys -t $session:0 "sudo openvpn $vpn" C-m

# Create new window to work in
tmux new-window -t $session -n $ip

# Add a delay to ensure zsh is properly initialized
tmux send-keys -t $session:1 "clear" C-m
tmux send-keys -t $session:1 "sleep .2" C-m 

# Call the scan_machine.sh script
tmux send-keys -t $session:1 "clear" C-m
tmux send-keys -t $session:1 "$HOME/scripts/scan_machine.sh $ip $session" C-m

# Create a new pane to work in
tmux split-window -h -t $session:1

# Attach to the tmux session
tmux attach -t $session
