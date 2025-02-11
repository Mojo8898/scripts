#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

color_codes = {
    "TARGET_COMPLETE": "\033[0;36m", # Cyan
    "NC": "\033[0m"
}

def main():
    # Define home directory
    home_dir = os.path.expanduser("~")

    # Initialize arguments
    parser = argparse.ArgumentParser(description="Execute scan_machine.py on a list of targets from a file.")
    parser.add_argument("targets_file", type=str, help="File containing the list of targets to scan separated by newlines")
    parser.add_argument("-S", "--scan_script_path", type=str, default=os.path.join(home_dir, "scripts", "scan_machine.py"), help="Path to nmap wrapper script (default: ~/scripts/scan_machine.py)")
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
                    ["python3", scan_script_path, target],
                    cwd=target,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                if e.returncode == 130:
                    print("\nCtrl+C detected. Exiting...")
                    sys.exit(130)
                print(f"Scan script failed for target {target} with error: {e}")
                continue
            divider = f"\n  {color_codes['TARGET_COMPLETE']}<==============================================================================================================>{color_codes['NC']}\n"
            print(divider)
            print(f"                                       {color_codes['TARGET_COMPLETE']}SCAN COMPLETE FOR TARGET: {target}{color_codes['NC']}")
            print(divider)

if __name__ == "__main__":
    main()
