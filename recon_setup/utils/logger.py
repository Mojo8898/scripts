import datetime

# Logging helper function
def write_log(log_file, message, level="INFO", note=None):
    color_codes = {
        "INFO": "\033[1;32m",      # Green
        "WARN": "\033[1;33m",      # Yellow
        "ERROR": "\033[1;31m",     # Red
        "TIMESTAMP": "\033[1;34m", # Blue
        "SUCCESS": "\033[1;35m",   # Magenta
        "NOTE": "\033[1;33m",      # Bold Yellow
        "NC": "\033[0m"
    }
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{color_codes['TIMESTAMP']}[{timestamp}]{color_codes['NC']} ")
        if note:
            f.write(f"{color_codes[level]}[{level}]{color_codes['NC']} {message} {color_codes['NOTE']}{note}{color_codes['NC']}\n")
        else:
            f.write(f"{color_codes[level]}[{level}]{color_codes['NC']} {message}\n")
