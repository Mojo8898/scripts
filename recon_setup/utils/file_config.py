import json
import subprocess
import textwrap
from pathlib import Path

from utils.logger import write_log


def populate_files(context):
    fqdn = context.get_target()
    # Write context files
    open(context.tmux_pipe_file, 'a').close()
    open(context.users_file, 'a').close()
    open(context.creds_file, 'a').close()
    # Write /etc/krb5.conf if a domain is detected
    if context.domain:
        default_realm = context.domain.upper()
        domain_realm = context.domain
        config_contents = textwrap.dedent(f"""\
            [libdefaults]
                default_realm = {default_realm}

            # The following krb5.conf variables are only for MIT Kerberos.
                kdc_timesync = 1
                ccache_type = 4
                forwardable = true
                proxiable = true
                rdns = false

            # The following libdefaults parameters are only for Heimdal Kerberos.
                fcc-mit-ticketflags = true

            [realms]
                {default_realm} = {{
                    kdc = {fqdn}
                    admin_server = {fqdn}
                }}

            [domain_realm]
                .{domain_realm} = {default_realm}
                {domain_realm} = {default_realm}
            """).strip()
        try:
            subprocess.run(
                ["sudo", "/usr/bin/tee", "/etc/krb5.conf"],
                input=config_contents,
                text=True,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else 'Unknown error'
            write_log(context.log_file, f"Failed to write to /etc/krb5.conf with error: {error_msg}", "ERROR")
        except Exception as e:
            write_log(context.log_file, f"Failed to write to /etc/krb5.conf with error: {str(e)}", "ERROR")


def add_creds(user, passwd):
    cfg = Path.home()/".aliasr.json"
    data = json.loads(cfg.read_text())
    data["user"] = [user]
    data["passwd"] = [passwd]
    cfg.write_text(json.dumps(data))
