#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

def print_separator(message=None):
    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80
    if message:
        odd = ""
        if (term_width - len(message)) % 2 == 1:
            odd = "="
        equal_space = (term_width - len(message) - 10) // 2
        separator = "   <" + "=" * equal_space + " " + message + " " + "=" * equal_space + odd + ">"
    else:
        separator = "   <" + "=" * (term_width - 8) + ">"
    print(f"\n\033[0;36m{separator}\033[0m\n")

def main():
    # Initialize arguments
    parser = argparse.ArgumentParser(description="Execute scan_machine.py on a list of targets from a file.")
    parser.add_argument("targets_file", type=str, help="File containing the list of targets to scan separated by newlines")
    parser.add_argument("-S", "--scan_script_path", type=str, default="/opt/scripts/scan_machine.py", help="Path to nmap wrapper script (default: /opt/scripts/scan_machine.py)")
    args = parser.parse_args()

    # Define local variables
    targets_file = args.targets_file
    scan_script_path = args.scan_script_path

    # Check required file paths
    if not os.path.isfile(targets_file):
        print(f"Targets file not found at {targets_file}")
        sys.exit(1)
    elif not os.path.isfile(scan_script_path):
        print(f"Error: Required file 'scan_machine.py' not found at {scan_script_path}", file=sys.stderr)
        sys.exit(1)

    # Open and iterate over each target in the targets file
    with open(targets_file, "r") as file:
        for line in file:
            target = line.strip()
            if not target:
                continue

            # Create target directory
            target_nmap_dir = os.path.join(target, "nmap")
            try:
                os.makedirs(target_nmap_dir, exist_ok=True)
            except OSError as e:
                print(f"Failed to create directory for target {target}: {e}")
                continue

            # Execute scan script
            try:
                subprocess.run(
                    [scan_script_path, target],
                    cwd=target,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else 'Unknown error'
                print(f"Failed to execute nmap wrapper script with error: {error_msg}")
            except Exception as e:
                print(f"Failed to execute nmap wrapper script with error: {str(e)}")
            print_separator(f"SCANNING COMPLETE FOR TARGET: {target}")

if __name__ == "__main__":
    main()
