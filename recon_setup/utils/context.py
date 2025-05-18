import os
import libtmux
import tempfile
from dataclasses import dataclass, field
from typing import Dict, Optional

from utils.file_config import populate_files,add_creds
from utils.hostfile import resolve_host
from utils.logger import write_log
from utils.spray import spray_passwd

@dataclass
class Context:
    """Represents the current tmux automation session context"""
    session: libtmux.Session
    nmap_pane: libtmux.Pane
    nmap_dir: str
    tmux_pipe_file: str
    log_file: str
    users_file: str
    creds_file: str
    ip: str
    _creds: Dict[str, str] = field(default_factory=dict)
    hostname: str = ""
    domain: str = ""
    vhost: str = ""
    task_window_count: int = 0
    current_task_window: Optional[libtmux.Window] = None
    current_task_pane: int = 0
    sprayable_ports: Dict[int, str] = field(default_factory=dict)
    is_ad: bool = False

    def __post_init__(self):
        """Initialize the context class"""
        self.hostname, self.domain, self.vhost = resolve_host(self.log_file, self.ip)
        populate_files(self)

    def creds_exist(self):
        return bool(self._creds)

    def get_initial_cred(self):
        try:
            return next(iter(self._creds.items()))
        except Exception as e:
            write_log(self.log_file, f"Failed to query initial cred due to error: {str(e)}")
            return None

    def get_target(self):
        """Determine the target string from hostname/domain/ip."""
        if self.hostname and self.domain:
            return f"{self.hostname}.{self.domain}"
        elif self.domain:
            return self.domain
        else:
            return self.ip

    def add_initial_cred(self, user: str, passwd: str = ""):
        """Add initial credential to creds file"""
        add_creds(user, passwd)
        with open(self.creds_file, "a") as f:
            f.write(f"{user}:{passwd}\n")
        self.add_cred(user, passwd)

    def add_cred(self, user: str, passwd: str = ""):
        """Add credential to _creds dictionary and users file"""
        # Create new credential
        self._creds[user] = passwd
        write_log(self.log_file, f"Added new user: {user}")
        # Add user to users file
        with open(self.users_file, "r") as f:
            for line in f:
                if user in line:
                    return
        with open(self.users_file, "a") as f:
            f.write(f"{user}\n")

    def spray_cred(self, user, passwd=None):
        target = self.get_target()
        if passwd:
            write_log(self.log_file, f"Spraying {passwd} against all available users/protocols...")
            spray_passwd(target, self.users_file, passwd, self.sprayable_ports, self.log_file)
        else:
            write_log(self.log_file, f"Spraying existing passwords against user: \"{user}\"...")
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                tmp.write(f"{user}\n")
                tmp_file = tmp.name
            for passwd in self._creds.values():
                if passwd:
                    spray_passwd(target, tmp_file, passwd, self.sprayable_ports, self.log_file)
            os.remove(tmp_file)

    def spray_users(self, users):
        target = self.get_target()
        write_log(self.log_file, f"Spraying users list against known passwords...")
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            for user in users:
                tmp.write(f"{user}\n")
            tmp_file = tmp.name
        for passwd in self._creds.values():
            if passwd:
                spray_passwd(target, tmp_file, passwd, self.sprayable_ports, self.log_file)
        os.remove(tmp_file)
