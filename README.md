# scripts

These are some of the scripts that I use regularly

## Install

```bash
git clone https://github.com/Mojo8898/scripts.git "$HOME/scripts"
find "$HOME/scripts" -type f -name "*.sh" -exec chmod +x {} +
```

## Example Usage

### scan_machine.sh

Running scan_machine.sh against the target ip address `10.129.228.217`

```bash
~/scripts/scan_machine.sh '10.129.228.217'
```

This will automatically launch a quick TCP scan with nmap, looking only for open ports before launching a targeted TCP scan + UDP scan

### htb_recon_setup.sh

Running htb_recon_setup.sh against the box `busqueda` with the target ip address `10.129.228.217`

```bash
~/scripts/htb/htb_recon_setup.sh 'busqueda' '10.129.228.217' ~/htb/lab_Mojo098.ovpn
```

This will automatically launch the VPN connection in the previous window and run scan_machine.sh against the target ip address in the left pane

### ps_cradle_gen.sh

Running ps_cradle_gen.sh with the `-l` option to set up a listener on port `9001` and give it our ip address of `10.10.14.82`

```bash
~/scripts/ps_cradle_gen.sh 10.10.14.82 9001 -l
```
You can exclude the `-l` option if you just want to copy the cradles and configure your own listener
