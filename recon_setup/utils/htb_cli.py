#!/usr/bin/env python3

import re
import requests
import subprocess
from datetime import datetime, timezone
from rich.console import Console
from time import sleep

def query_ip(machine):
    try:
        result = subprocess.run(
            ["htb-cli", "start", "-m", f"{machine}", "--batch"],
            capture_output=True,
            check=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else 'Unknown error'
        print(f"Failed to execute htb-cli with error: {error_msg}", "ERROR")
    except Exception as e:
       print(f"Failed to execute htb-cli with error: {str(e)}", "ERROR")
    match = re.search(r"Target:\s+(\d+\.\d+\.\d+\.\d+)", result.stdout)
    if match:
        ip = match.group(1)
        return ip
    else:
        return None

def get_current_time():
    try:
        response = requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC")
        response.raise_for_status()
        data = response.json()
        iso_str = data.get("datetime")
        if iso_str.endswith('Z'):
            iso_str = iso_str.replace('Z', '+00:00')
        return datetime.fromisoformat(iso_str)
    except Exception as e:
        print("Error fetching time from API, falling back to local time:", e)
        return datetime.now(timezone.utc)

def wait_for_release(console):
    now = get_current_time()
    print(f"Current time: {now}")
    release_time = now.replace(hour=19, minute=0, second=0, microsecond=0)
    if now > release_time:
        print("Release time (7pm UTC) has already passed, continuing...")
        return
    wait_seconds = (release_time - now).total_seconds()
    try:
        with console.status(f"Waiting {wait_seconds} seconds until release time (7pm UTC)...", spinner="dots"):
            sleep(wait_seconds)
    except KeyboardInterrupt:
        print("Ctrl+C detected. Spawning machine now instead of waiting...")

def spawn_machine(machine, new_release):
    console = Console()
    if new_release:
        wait_for_release(console)
    with console.status("Spawning machine...", spinner="dots"):
        ip = query_ip(machine)
    return ip
