# scripts

These are some of the scripts that I use regularly

## Install

```bash
git clone https://github.com/Mojo8898/scripts.git "$HOME/scripts"
find "$HOME/scripts" -type f -name "*.sh" -exec chmod +x {} +
```

## Usage

Run htb_recon_setup.sh against the box "busqueda" with the given ip address "10.129.228.217". Make sure you change the VPN path.

```bash
~/scripts/htb/htb_recon_setup.sh 'busqueda' '10.129.228.217' ~/htb/lab_Mojo098.ovpn
```

Once executed, you can view your nmap scans on the left pane. Leave the top right pane alone until the nmap scans are finished so that automated scripts can run immediately when ports are discovered during the nmap scan.

you can still resize/split any of the panes or create a new window to work in if you so desire.
