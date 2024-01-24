# scripts

These are some of the scripts that I use regularly

## Install

```bash
git clone https://github.com/Mojo8898/scripts.git "$HOME/scripts"
find "$HOME/scripts" -type f -name "*.sh" -exec chmod +x {} +
```

## Example Usage

### scan_machine.sh

Run scan_machine.sh against the target ip address `10.129.228.217`

```bash
~/scripts/scan_machine.sh '10.129.228.217'
```

This will automatically launch a quick TCP scan with nmap, looking only for open ports before launching a targeted TCP scan + UDP scan

### scan_host_list.sh

Run scan_host_list.sh against the the host list `external_hosts.exe`. This file contains a list of target ip addresses separated by newlines

```bash
~/scripts/scan_host_list.sh external_hosts.txt
```

This will automatically loop through hosts in `external_hosts.txt`, creating directories for each of them and executing `scan_machine.sh`

### ps_cradle_gen.sh

Run ps_cradle_gen.sh with the `-l` option to set up a listener on port `9001` and give it our ip address of `10.10.14.82`

```bash
~/scripts/ps_cradle_gen.sh 10.10.14.82 9001
```

This will generate a list of cradles you can utilize to pop shells in Windows environments

You can also include the `-l` option to start a listener

### htb_recon_setup.sh

Run htb_recon_setup.sh against the box `busqueda` with the target ip address `10.129.228.217`, specifying the VPN file `~/htb/lab_Mojo098.ovpn`

```bash
~/scripts/htb_recon_setup.sh 'busqueda' '10.129.228.217' ~/htb/lab_Mojo098.ovpn
```

This will automatically launch the VPN connection in the previous window and run scan_machine.sh against the target ip address in the left pane

Default path created for session: `$HOME/htb/machines/$session/nmap`

### oscp_recon_setup.sh

Run oscp_recon_setup for the lab `lab01` with the VPN file `~/oscp/universal.ovpn`

```bash
~/scripts/oscp_recon_setup.sh lab01 ~/oscp/universal.ovpn
```

Default path created for session: `$HOME/oscp/labs/$session`
