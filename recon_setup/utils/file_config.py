import os
import subprocess
import textwrap

from utils.logger import write_log

def populate_files(context):
    target = context.get_target()
    # Write context files
    open(context.tmux_pipe_file, 'a').close()
    open(context.users_file, 'a').close()
    open(context.creds_file, 'a').close()
    # Write arsenal data
    arsenal_entry = f'{{"ip": "{context.ip}", "dc_ip": "{context.ip}", "target": "{target}", "domain": "{context.domain or ""}", "domain_name": "{context.domain or ""}", "user": "", "file": ""}}'
    home_dir = os.path.expanduser("~")
    arsenal_globals_file = os.path.join(home_dir, ".arsenal.json")
    with open(arsenal_globals_file, 'w') as f:
        f.write(arsenal_entry)
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
                    kdc = {target}
                    admin_server = {target}
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
