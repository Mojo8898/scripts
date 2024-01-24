#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <hosts_file>"
    exit 1
fi

hosts_file=$1
scan_script="$HOME/scripts/scan_machine.sh"

# Check if scan script exists
if [ ! -f "$scan_script" ]; then
    echo "Scan script not found at $scan_script"
    exit 1
fi

# Loop through each line in hosts file
while IFS= read -r host; do
    # Skip empty lines
    if [ -z "$host" ]; then
        continue
    fi

    # Create a directory for the host if it doesn't exist
    mkdir -p "$host"
    if [ $? -ne 0 ]; then
        echo "Failed to create directory for host $host"
        continue
    fi

    # Scan hosts within respective directories
    cd "$host"
    bash "$scan_script" "$host"
    cd ..

    echo -e '\n<== SCAN COMPLETE FOR HOST $host ==>\n'
done < "$hosts_file"
