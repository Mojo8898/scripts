#!/usr/bin/python3

import argparse
import os
import re
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
    print(f"\n\033[0;32m{separator}\033[0m\n")

def was_scan_completed(filepath):
    """Check if the file exists, is non-empty, and has more than one line."""
    if not os.path.isfile(filepath):
        return False
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        return len(lines) > 1
    except Exception:
        return False

def run_command(cmd):
    """Run a command and let its stdout/stderr go to the terminal."""
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nCtrl+C detected; aborting current scan.")
    except subprocess.CalledProcessError as e:
        if e.returncode == -2:
            print("\nCtrl+C detected; aborting current scan.")
            return
        error_msg = e.stderr.strip() if e.stderr else 'Unknown error'
        print(f"Failed to execute scan_machine.py with error: {error_msg}")
        print(e.returncode)
        sys.exit(e.returncode)

def cat_file(filepath):
    """Print the content of the file to stdout."""
    try:
        with open(filepath, 'r') as f:
            sys.stdout.write(f.read())
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

def extract_open_ports(full_tcp_file):
    """Extract open ports from the full TCP scan file."""
    open_ports = []
    try:
        with open(full_tcp_file, 'r') as f:
            for line in f:
                line = line.strip()
                if re.match(r'^\d', line) and "open" in line:
                    tokens = line.split()
                    if tokens:
                        port = tokens[0].split('/')[0]
                        open_ports.append(port)
    except FileNotFoundError:
        pass
    return ",".join(open_ports)

def main():
    # Initialize arguments
    parser = argparse.ArgumentParser(description="Wrapper for nmap scans")
    parser.add_argument("ip", type=str, help="IP address of the target machine")
    parser.add_argument("-l", "--lightweight", action="store_true", help="Lightweight TCP scan")
    args = parser.parse_args()

    # Define local variables
    ip = args.ip
    lightweight = args.lightweight

    # Create nmap directory
    nmap_dir = "nmap"
    try:
        os.makedirs(nmap_dir, exist_ok=True)
    except Exception as e:
        print(f"Failed to create {nmap_dir} directory: {e}")
        sys.exit(1)

    # Define file paths
    lightweight_tcp_file = os.path.join(nmap_dir, "lightweight.nmap")
    full_tcp_file = os.path.join(nmap_dir, "full_tcp.nmap")
    targeted_tcp_file = os.path.join(nmap_dir, "targeted_tcp.nmap")
    open_tcp_file = os.path.join(nmap_dir, "open_tcp.txt")
    udp_file = os.path.join(nmap_dir, "udp.nmap")

    if lightweight:

        # Lightweight TCP scan
        print_separator("Launching lightweight TCP scan...")
        run_command(["sudo", "/usr/bin/nmap", "-Pn", "-n", "-sT", "-p", "21,22,23,25,53,80,88,110,111,135,137,139,143,389,443,445,636,993,995,1433,2049,3268,3269,3306,3389,5900,5985,8080", "--open", "-oN", lightweight_tcp_file, ip])
    else:
        if not was_scan_completed(targeted_tcp_file):

            # Quick TCP scan
            print_separator("Launching quick TCP scan...")
            run_command(["sudo", "/usr/bin/nmap", "-Pn", "-n", "--top-ports", "3000", "-sCV", "--min-rate", "1000", "-v", ip])

            # Full TCP scan
            print_separator("Launching full TCP scan...")
            run_command(["sudo", "/usr/bin/nmap", "-Pn", "-n", "-p-", "--min-rate", "1000", "-oN", full_tcp_file, ip])

            # Extract open ports for targeted TCP scan
            ports = extract_open_ports(full_tcp_file)
            try:
                with open(open_tcp_file, "w") as f:
                    f.write(ports)
            except Exception as e:
                print(f"Error writing to {open_tcp_file}: {e}")

            # Targeted TCP scan
            if ports:
                print_separator("Launching targeted TCP scan...")
                run_command(["sudo", "/usr/bin/nmap", "-Pn", "-n", "-p", ports, "-sCV", "-oN", targeted_tcp_file, ip])
            else:
                print("\nFull TCP scan was not completed. Skipping targeted TCP scan...")
        else:
            print_separator("Targeted TCP scan already completed")
            cat_file(targeted_tcp_file)

        # UDP Scan
        if not was_scan_completed(udp_file):
            print_separator("Launching UDP scan...")
            run_command(["sudo", "/usr/bin/nmap", "-Pn", "-n", "-sUV", "-T4", "--top-ports", "200", "-oN", udp_file, "-v", ip])
        else:
            print_separator("UDP scan already completed")
            cat_file(udp_file)
        print()

if __name__ == "__main__":
    main()
