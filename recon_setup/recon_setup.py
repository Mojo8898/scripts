#!/usr/bin/python3

import argparse
import ctypes
import libtmux
import os
import signal
import subprocess
import sys
from time import sleep

from utils.context import Context
from utils.htb_cli import spawn_machine
from watchers.nmap_watcher import watch_nmap

def set_death_signal(sig=signal.SIGHUP):
    """Send SIGHUP to the forked process when its parent dies"""
    libc = ctypes.CDLL("libc.so.6")
    PR_SET_PDEATHSIG = 1
    libc.prctl(PR_SET_PDEATHSIG, sig)

def verify_connection(ip):
    """Verify connection with target IP."""
    reachable = False
    while not reachable:
        try:
            subprocess.check_call(
                ["ping", "-c1", "-W.5", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            reachable = True
        except subprocess.CalledProcessError:
            reachable = False
        sleep(0.5)
    sleep(1)

def main():
    # Initialize parser
    parser = argparse.ArgumentParser(description="Automate the setup and enumeration process for offensive security labs.")

    # Initialize session arguments
    session_group = parser.add_argument_group("Session Arguments", "Arguments related to session configuration")
    session_group.add_argument("session_name", type=str, help="Name of the tmux session to be created")
    session_group.add_argument("-v", "--vpn_path", type=str, help="Path of your VPN file")
    session_group.add_argument("-s", "--session_path", type=str, default="/workspace/machines", help="Path to where the session will be created (default: /workspace/machines)")
    session_group.add_argument("-i", "--ip", type=str, help="IP address of the target machine")

    # Initialize HTB CLI arguments
    htb_cli_group = parser.add_argument_group("HTB CLI Arguments", "Arguments related to HTB CLI functionality")
    htb_cli_group.add_argument("--spawn", type=str, help="Spawn the target machine using the HTB CLI instead of providing an IP (requires htb-cli)")
    htb_cli_group.add_argument("-n", "--new_release", action="store_true", help="Wait for the scheduled release time (7pm UTC) and spawn automatically")

    # Initialize automation arguments
    automation_group = parser.add_argument_group("Automation Arguments", "Arguments related to automated tasking")
    automation_group.add_argument("-a", "--automate", action="store_true", help="Optional flag to enable automated tasks on the fly from nmap scan results")
    automation_group.add_argument("-u", "--username", type=str, help="Username to supply automated tasks (AD only)")
    automation_group.add_argument("-p", "--password", type=str, help="Password to supply automated tasks (AD only)")
    automation_group.add_argument("-d", "--debug", action="store_true", help="Enable debug mode for automation")

    # Initialize parser
    args = parser.parse_args()

    # Define local variables
    session_name = args.session_name
    vpn_path = os.path.abspath(args.vpn_path)
    session_path = args.session_path
    ip = args.ip
    spawn = args.spawn
    new_release = args.new_release
    automate = args.automate
    user = args.username
    passwd = args.password
    debug = args.debug

    # Define file paths
    scan_script_file = "/opt/scripts/scan_machine.py"
    target_dir = os.path.join(session_path, session_name)
    nmap_dir = os.path.join(target_dir, "nmap")
    log_dir = os.path.join(target_dir, "logs")
    tmux_pipe_file = os.path.join(log_dir, "tmux_pipe.log")
    log_file = os.path.join(log_dir, "task.log")
    debug_file = os.path.join(log_dir, "debug.log")
    users_file = os.path.join(target_dir, "valid_users.txt")
    creds_file = os.path.join(target_dir, "creds.txt")

    # Check for nmap wrapper script
    if not os.path.isfile(scan_script_file):
        print(f"Error: Required nmap wrapper script not found at {scan_script_file}", file=sys.stderr)
        sys.exit(1)

    # Initialize HTB machine if relevant arguments are included
    if spawn:
        ip = spawn_machine(spawn, new_release)
        if not ip:
            print("Error: HTB CLI failed to provide an IP")
            sys.exit(1)
    else:
        ip = args.ip

    # Initialize environment
    os.makedirs(nmap_dir, exist_ok=True)
    os.chdir(target_dir)

    # Initialize tmux session
    server = libtmux.Server()
    session = server.new_session(
        session_name=session_name,
        window_name="services",
        attach=False
    )
    initial_window = session.active_window
    openvpn_pane = initial_window.active_pane
    if os.path.isfile(vpn_path):
        openvpn_pane.send_keys(f"sudo openvpn {vpn_path}")
    ligolo_pane = openvpn_pane.split(direction=libtmux.pane.PaneDirection.Below)
    ligolo_pane.send_keys("mkdir -p ligolo; cd ligolo; proxy -selfcert")
    updog_pane = ligolo_pane.split(direction=libtmux.pane.PaneDirection.Right)
    updog_pane.send_keys("updog -p 8000 -d ~/staging")
    smbserver_pane = updog_pane.split(direction=libtmux.pane.PaneDirection.Below, size=20)
    smbserver_pane.send_keys("smbserver.py -smb2support a . -username mojo -password 'Password123!'")
    base_window = session.new_window(window_name=ip)

    # Initialize panes
    nmap_pane = base_window.active_pane
    base_pane = base_window.split(direction=libtmux.pane.PaneDirection.Right)

    # Fork process to attach to tmux session while executing additional tasks
    pid = os.fork()
    if pid == 0:
        set_death_signal()

        # Establish connection with VPN and initialize the base window
        if os.path.isfile(vpn_path):
            verify_connection(ip)
            sleep(1)
        session.select_window(1)
        base_pane.select()

        # Initialize automation if argument is provided
        if automate:
            os.makedirs(log_dir, exist_ok=True)
            for file in [tmux_pipe_file, log_file, debug_file, users_file, creds_file]:
                if os.path.isfile(file):
                    os.remove(file)

            # Initialize stdio depending on debug flag
            with open(os.devnull, "wb") as null:
                if debug:
                    with open(debug_file, "wb") as log:
                        os.dup2(null.fileno(), 0)
                        os.dup2(log.fileno(), 1)
                        os.dup2(log.fileno(), 2)
                else:
                    os.dup2(null.fileno(), 0)
                    os.dup2(null.fileno(), 1)
                    os.dup2(null.fileno(), 2)

            # Initialize context
            context = Context(session, nmap_pane, nmap_dir, tmux_pipe_file, log_file, users_file, creds_file, ip)
            if user and passwd:
                context.add_initial_cred(user.lower(), passwd=passwd)

            # Initialize task logging
            log_pane = base_pane.split(size=20)
            sleep(1)
            log_pane.send_keys(f"clear && tail -n +0 -f {log_file}")

            # Initialize nmap scanning and automation
            os.remove(tmux_pipe_file)
            nmap_pane.cmd("pipe-pane", f"cat >> {tmux_pipe_file}")
            nmap_pane.send_keys(f"{scan_script_file} {ip}")
            watch_nmap(context)
        elif ip:
            nmap_pane.send_keys(f"{scan_script_file} {ip}")
        os._exit(0)
    else:
        os.execvp("tmux", ["tmux", "attach-session", "-t", session_name])

if __name__ == "__main__":
    main()
