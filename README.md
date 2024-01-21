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
