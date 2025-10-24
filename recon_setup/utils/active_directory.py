import re
import subprocess

from utils.logger import write_log

_NEGATIVE = re.compile(r"\[\-\]")


def anonymous_bind(context):
    cmd = ["nxc", "ldap", context.ip, "-u", "", "-p", ""]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
    except Exception as e:
        write_log(context.log_file, f"NetExec ldap subprocess error: {e}", "ERROR")
        return False
    out = p.stdout or ""
    return not _NEGATIVE.search(out)


def enum_smb_shares(context):
    def run_nxc(user, passwd):
        cmd = f"nxc smb {context.ip} -u {user} "
        if passwd:
            cmd += f"-p '{passwd}' -k "
        else:
            cmd += f"-p '' "
        cmd += f"--shares"
        # write_log(context.log_file, f"Running: {cmd}", "INFO")
        try:
            p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8, check=False)
            return p.stdout or ""
        except Exception as e:
            write_log(context.log_file, f"Subprocess exception: {e}", "ERROR")
            return ""

    def parse_shares(raw):
        lines = [ln.rstrip("\n") for ln in raw.splitlines()]
        hdr_idx = None
        for i, ln in enumerate(lines):
            if "Share" in ln and "Permissions" in ln and "Remark" in ln:
                hdr_idx = i
                break
        if hdr_idx is None or hdr_idx + 2 >= len(lines):
            return []

        header = lines[hdr_idx]
        try:
            c_share = header.index("Share")
            c_perm = header.index("Permissions")
            c_remark = header.index("Remark")
        except ValueError:
            return []

        shares = []
        for ln in lines[hdr_idx + 2 :]:
            if "SMB" not in ln or not ln.strip() or ln.strip().startswith("-----"):
                continue
            pad = ln + " " * max(0, c_remark + 1 - len(ln))
            name = pad[c_share:c_perm].strip()
            perms = pad[c_perm:c_remark].strip()
            remark = pad[c_remark:].strip()
            if not name or name.startswith("-----"):
                continue
            access = [p.strip() for p in perms.split(",") if p.strip()] if perms else []
            shares.append({"name": name, "remark": remark, "access": access})

        return shares

    # 1) user/pass
    if context.creds_exist():
        user, passwd = context.get_initial_cred()
        if user is not None:
            out = run_nxc(user, passwd)
            shares = parse_shares(out)
            if shares:
                return shares, "user/pass"
            write_log(context.log_file, "Share enum with provided credentials failed; trying null session", "INFO")

    # 2) null
    out = run_nxc("''", "")
    shares = parse_shares(out)
    if shares:
        write_log(context.log_file, "Null authentication is enabled for reading shares", "SUCCESS")
        return shares, "null"

    # 3) guest
    out = run_nxc("a", "")
    shares = parse_shares(out)
    if shares:
        write_log(context.log_file, "Guest authentication is enabled for reading shares", "SUCCESS")
        return shares, "guest"

    return None, None
