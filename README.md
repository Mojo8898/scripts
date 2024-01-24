# scripts

These are some of the scripts that I use regularly

## Install

```bash
git clone https://github.com/Mojo8898/scripts.git "$HOME/scripts"
find "$HOME/scripts" -type f -name "*.sh" -exec chmod +x {} +
```

## Usage

### htb_recon_setup.sh

In the following example, we run htb_recon_setup.sh against the box "busqueda" with the given ip address "10.129.228.217".

```bash
~/scripts/htb/htb_recon_setup.sh 'busqueda' '10.129.228.217' ~/htb/lab_Mojo098.ovpn
```

You can view your nmap scans on the left pane and run commands on the right while you wait for your nmap scans to finish.

### ps_cradle_gen.sh

In the following example, we run ps_cradle_gen.sh with the `-l` option to set up a listener on port "9001" and give it our ip address of "10.10.14.82"

```bash
~/scripts/ps_cradle_gen.sh 10.10.14.82 9001 -l
```
