#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <session> <vpn_file>"
    exit 1
fi

session=$1
vpn=$2

# Create working environment
mkdir -p "$HOME/htb/prolabs/$session"
if [ $? -ne 0 ]; then
    echo "Failed to create directory for session $session"
    exit 1
fi
cd "$HOME/htb/prolabs/$session"

# Start tmux session
tmux new-session -d -s $session

# Connect to VPN
tmux send-keys -t $session:0 "clear" C-m
tmux rename-window -t $session:0 "openvpn"
tmux send-keys -t $session:0 "sudo openvpn $vpn" C-m

# Create new window to work in
tmux new-window -t $session
tmux send-keys -t $session:1 "clear" C-m
tmux send-keys -t $session:1 "sleep .2" C-m
tmux send-keys -t $session:1 "clear" C-m

# Create a new pane to dynamically view recommended commands based on nmap output
tmux split-window -h -t $session:1
tmux send-keys -t $session:1 "clear" C-m
tmux send-keys -t $session:1 "sleep .2" C-m
tmux send-keys -t $session:1 "clear" C-m

# Attach to the tmux session
tmux attach -t $session
