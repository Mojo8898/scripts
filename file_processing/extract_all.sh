#!/bin/bash

# Function to extract files
extract_file() {
    local file=$1
    local folder=$2

    case $file in
        *.tar.bz2)   tar xvjf "$file" -C "$folder" ;;
        *.tar.gz)    tar xvzf "$file" -C "$folder" ;;
        *.bz2)       mkdir -p "$folder" && bunzip2 -c "$file" > "$folder/${file%.bz2}" ;;
        *.rar)       unrar x "$file" "$folder/" ;;
        *.gz)        mkdir -p "$folder" && gunzip -c "$file" > "$folder/${file%.gz}" ;;
        *.tar)       tar xvf "$file" -C "$folder" ;;
        *.tbz2)      tar xvjf "$file" -C "$folder" ;;
        *.tgz)       tar xvzf "$file" -C "$folder" ;;
        *.zip)       unzip "$file" -d "$folder" ;;
        *.Z)         mkdir -p "$folder" && uncompress -c "$file" > "$folder/${file%.Z}" ;;
        *.7z)        7z x "$file" -o"$folder" ;;
        *)           echo "don't know how to extract '$file'..." ;;
    esac
}

# Main loop through all files in the current directory
for file in *; do
    if [ -f "$file" ]; then
        # Create a directory based on the filename
        folder_name=$(basename "$file")
        folder_name="${folder_name%.*}_extracted"
        mkdir -p "$folder_name"

        # Extract the file into the created directory
        extract_file "$file" "$folder_name"
    fi
done

