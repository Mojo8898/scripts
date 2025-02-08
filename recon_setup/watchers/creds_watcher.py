import os
from threading import Event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils.logger import write_log

class CredsFileHandler(FileSystemEventHandler):
    """Monitors nmap log file for open ports and scan completion"""
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.completed = Event() # Event to signal scan completion

    def on_modified(self, event):
        if event.src_path == self.context.creds_file:
            with open(event.src_path, 'r') as file:
                lines = file.read().splitlines()
            if not lines:
                return
            last_line = None
            for line in reversed(lines):
                if line.strip():
                    last_line = line.strip()
                    break
            if last_line:
                parts = line.split(':', 1)
                if len(parts) != 2:
                    write_log(self.context.log_file, f"Creds observer encountered malformed credential in creds.txt", "WARN")
                    return
                user, passwd = parts
                self.context.add_cred(user, passwd)
                self.context.spray_cred(user, passwd)
                self.completed.set() # Signal that scan is complete

def watch_creds(context):
    # Initialize nmap log handler and observer
    event_handler = CredsFileHandler(context)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(context.creds_file), recursive=False)
    # Start the observer
    observer.start()
    try:
        event_handler.completed.wait()
    except Exception as e:
        write_log(context.log_file, f"Creds observer interrupted: {str(e)}", "ERROR")
    finally:
        observer.stop()
        observer.join()
