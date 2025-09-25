import re
import subprocess

from impacket.smbconnection import SMBConnection

from utils.logger import write_log


_NEGATIVE = re.compile(r"\[\-\]")


def anonymous_bind(context) -> bool:
    cmd = ["nxc", "ldap", context.ip, "-u", "", "-p", ""]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
    out = p.stdout or ""
    if _NEGATIVE.search(out):
        return False
    else:
        return True


def enum_smb_shares(context) -> list:
    """Enumerates SMB shares and their access permissions."""
    shares_info = []
    if context.creds_exist():
        try:
            conn = SMBConnection(context.ip, context.ip)
            user, passwd = context.get_initial_cred()
            conn.login(user, passwd)
            shares = conn.listShares()
            method = 'user/pass'
        except Exception as e:
            write_log(context.log_file, f"Failed to list shares with provided credentials", "WARN")
    else:
        try:
            conn = SMBConnection(context.ip, context.ip)
            conn.login('', '') # Null session
            shares = conn.listShares()
            write_log(context.log_file, f"Null authentication is enabled for reading shares", "SUCCESS")
            method = 'null'
        except:
            try:
                conn = SMBConnection(context.ip, context.ip)
                conn.login('a', '') # Guest authentication
                shares = conn.listShares()
                write_log(context.log_file, f"Guest authentication is enabled for reading shares", "SUCCESS")
                method = 'guest'
            except:
                return None, None
        for share in shares:
            share_name = share['shi1_netname'][:-1]  # Remove trailing null byte
            share_remark = share['shi1_remark'][:-1] if share['shi1_remark'] else ""
            access = []
            # Check READ access (list files)
            try:
                conn.listPath(share_name, "*")
                access.append("READ")
            except Exception:
                pass
            # Check WRITE access (create/delete dir/file)
            try:
                temp_dir = f"\\bigbeans"
                conn.createDirectory(share_name, temp_dir)
                conn.deleteDirectory(share_name, temp_dir)
                access.append("WRITE")
            except Exception:
                pass
            shares_info.append({
                "name": share_name,
                "remark": share_remark,
                "access": access
            })
    conn.logoff()
    return shares_info, method
