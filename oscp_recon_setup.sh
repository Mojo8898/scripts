#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <session>"
    exit 1
fi

session=$1

# Create working environment
mkdir -p "$HOME/oscp/labs/$session"
cd "$HOME/oscp/labs/$session"

# Start tmux session
tmux new-session -d -s $session
tmux set-environment -t $session SESSION "$session"

# Connect to VPN
tmux send-keys -t $session:0 "clear" C-m
tmux rename-window -t $session:0 "openvpn"

# Create new window to work in
tmux new-window -t $session

# Create a new pane to dynamically view recommended commands based on nmap output
tmux split-window -h -t $session:1

# Attach to the tmux session
tmux attach -t $session