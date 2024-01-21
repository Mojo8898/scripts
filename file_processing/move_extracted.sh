#!/bin/bash

# Check if the destination directory is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 destination_directory"
    exit 1
fi

destination=$1

# Create the destination directory if it does not exist
if [ ! -d "$destination" ]; then
    mkdir -p "$destination"
fi

# Move the extracted folders to the destination directory
for folder in *_extracted; do
    if [ -d "$folder" ]; then
        echo "Moving $folder to $destination"
        mv "$folder" "$destination"
    fi
done

