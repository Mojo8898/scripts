import requests
import subprocess
import urllib3
from impacket.smbconnection import SMBConnection

from utils.logger import write_log

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def add_entry(log_file, entry):
    """Handle hostfile generation and return hostname/domain"""
    # Check if entry exists
    with open("/etc/hosts", "r") as f:
        content = f.read()
        ip = entry.split()[0]
        if ip in content:
            write_log(log_file, f"/etc/hosts entry already exists for {ip}", "WARN")
            return
    try:
        subprocess.run(
            ['sudo', '/usr/bin/tee', '-a', '/etc/hosts'],
            input=f"{entry}\n",
            text=True,
            check=True,
            capture_output=True
        )
        write_log(log_file, f"Added host entry: {entry}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else 'Unknown error'
        write_log(log_file, f"Failed to write to /etc/hosts with error: {error_msg}", "ERROR")
    except Exception as e:
        write_log(log_file, f"Failed to write to /etc/hosts with error: {str(e)}", "ERROR")

def resolve_host(log_file, ip):
    try:
        conn = SMBConnection(ip, ip, timeout=1)
        conn.login("", "")
        hostname = conn.getServerName()
        domain = conn.getServerDNSDomainName()
        conn.logoff()

        if not domain or hostname == domain:
            entry = f"{ip}\t{hostname}"
        else:
            entry = f"{ip}\t{hostname} {hostname}.{domain} {domain}"
        add_entry(log_file, entry)
        return hostname, domain, None
    except Exception as e:
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
                    return None, domain, vhost
                else:
                    write_log(log_file, f"Missing \"location\" in HTTP response headers", "WARN")
            except Exception as e:
                pass
        write_log(log_file, "Failed to resolve hostname/domain", "WARN")
        return None, None, None
