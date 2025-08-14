import re
import requests
import subprocess
import urllib3

from utils.logger import write_log

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def add_entry(log_file, entry):
    """Handle hostfile generation and return hostname/domain"""
    # Check if entry exists
    parts = entry.split()
    if not parts:
        write_log(log_file, "Empty entry provided.", "ERROR")
        return
    new_ip = parts[0]
    new_hosts = set(host.lower() for host in parts[1:])
    try:
        with open("/etc/hosts", "r") as f:
            lines = f.readlines()
    except Exception as e:
        write_log(log_file, f"Failed to read /etc/hosts: {str(e)}", "ERROR")
        return
    filtered_lines = []
    removed_entries = []
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            filtered_lines.append(line)
            continue
        line_parts = stripped_line.split()
        if not line_parts:
            filtered_lines.append(line)
            continue
        line_ip = line_parts[0]
        line_hosts = set(host.lower() for host in line_parts[1:])
        if line_ip == new_ip or new_hosts.intersection(line_hosts):
            removed_entries.append(stripped_line)
            continue
        filtered_lines.append(line)
    filtered_lines.append(entry + "\n")
    new_content = "".join(filtered_lines)
    try:
        subprocess.run(
            ['sudo', '/usr/bin/tee', '/etc/hosts'],
            input=new_content,
            text=True,
            check=True,
            capture_output=True
        )
        write_log(log_file, f"Added /etc/hosts entry: {entry}")
        if removed_entries:
            removed_str = ", ".join(removed_entries)
            write_log(log_file, f"- Removed conflicting entries: {removed_str}", "WARN")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else 'Unknown error'
        write_log(log_file, f"Failed to write to /etc/hosts with error: {error_msg}", "ERROR")
    except Exception as e:
        write_log(log_file, f"Failed to write to /etc/hosts with error: {str(e)}", "ERROR")

def resolve_host(log_file, ip):
    cmd = f"nxc ldap {ip}"
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=2
        )
        stdout = result.stdout
    except Exception as e:
        stdout = None
        write_log(log_file, f"NetExec ldap subprocess error: {str(e)}", "ERROR")
    if not (stdout or '').strip():
        cmd = f"nxc smb {ip}"
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                text=True,
                capture_output=True,
                timeout=2
            )
            stdout = result.stdout
        except Exception as e:
            stdout = None
            write_log(log_file, f"NetExec smb subprocess error: {str(e)}", "ERROR")
        if not (stdout or '').strip():
            for scheme in ['http', 'https']:
                try:
                    response = requests.get(
                        f"{scheme}://{ip}",
                        allow_redirects=False,
                        timeout=2,
                        verify=False
                    )
                    if response.is_redirect and 'location' in response.headers:
                        fqdn = response.headers['location'].split('//')[-1].split('/')[0]
                        fqdn_parts = fqdn.split('.')
                        if len(fqdn.split('.')) > 2:
                            vhost = fqdn
                            domain = '.'.join(fqdn_parts[1:])
                            entry = f"{ip}\t{fqdn} {domain}"
                            write_log(log_file, f"Vhost discovered: {vhost}")
                        else:
                            vhost = None
                            domain = fqdn
                            entry = f"{ip}\t{domain}"
                        add_entry(log_file, entry)
                        write_log(log_file, f"Adding entry to hosts: {entry}")
                        return None, domain, vhost
                    else:
                        write_log(log_file, f"Missing \"location\" in HTTP response headers", "WARN")
                except Exception as e:
                    pass
            write_log(log_file, "Failed to resolve hostname/domain", "WARN")
            return None, None, None
        else:
            hostname = re.search(r"\(name:([^)]+)\)", result.stdout).group(1)
            domain = re.search(r"\(domain:([^)]+)\)", result.stdout).group(1)
            if not domain or hostname == domain:
                entry = f"{ip}\t{hostname}"
            else:
                entry = f"{ip}\t{hostname} {hostname}.{domain} {domain}"
            add_entry(log_file, entry)
            return hostname, domain, None
    else:
        hostname = re.search(r"\(name:([^)]+)\)", result.stdout).group(1)
        domain = re.search(r"\(domain:([^)]+)\)", result.stdout).group(1)
        if not domain or hostname == domain:
            entry = f"{ip}\t{hostname}"
        else:
            entry = f"{ip}\t{hostname} {hostname}.{domain} {domain}"
        add_entry(log_file, entry)
        return hostname, domain, None