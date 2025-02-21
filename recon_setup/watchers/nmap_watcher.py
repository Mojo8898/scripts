import os
from threading import Event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils.tasks import handle_task
from utils.logger import write_log
from utils.spray import start_spraying

class NmapLogHandler(FileSystemEventHandler):
    """Monitors nmap log file for open ports and scan completion"""
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.last_position = 0
        self.completed = Event() # Event to signal scan completion

    def on_modified(self, event):
        if event.src_path == self.context.tmux_pipe_file:
            with open(self.context.tmux_pipe_file, 'r') as tmux_pipe_file:
                tmux_pipe_file.seek(self.last_position)
                new_lines = tmux_pipe_file.readlines()
                self.last_position = tmux_pipe_file.tell()

                for line in new_lines:
                    if "Discovered open port" in line:
                        parts = line.split()
                        port = parts[3].split('/')[0]
                        handle_task(self.context, port)
                    elif "Completed SYN Stealth" in line or "full TCP" in line:
                        self.context.nmap_pane.cmd("pipe-pane")
                        if "<" in line:
                            open_tcp_file = os.path.join(self.context.nmap_dir, "open_tcp.txt")
                            with open(open_tcp_file, 'r') as open_ports_file:
                                data = open_ports_file.read().strip()
                                ports = data.split(',')
                                for port in ports:
                                    handle_task(self.context, port)
                        self.completed.set() # Signal that scan is complete

def watch_nmap(context):
    # Initialize nmap log handler and observer
    event_handler = NmapLogHandler(context)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(context.tmux_pipe_file), recursive=False)
    # Start the observer
    observer.start()
    try:
        event_handler.completed.wait()
    except Exception as e:
        write_log(context.log_file, f"Nmap observer interrupted: {str(e)}", "ERROR")
    finally:
        write_log(context.log_file, "Initial nmap scan complete - stopping nmap observer")
        observer.stop()
        observer.join()
        if context.is_ad:
        # if True:
            write_log(context.log_file, "Machine identified as domain controller, watching for credentials to spray...")
            start_spraying(context)
