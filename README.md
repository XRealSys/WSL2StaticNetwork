[中文文档]: README_CHINESE.md

You can also visit: [中文文档]
---

**WSL2(Windows Subsystem for Linux 2)** provides a virtual machine that allows us to use linux on windows. But without discussing its other problems, its default DHCP network allocation method makes users feel inconvenient. <br>
*How to solve the problem of DHCP?*<br>
*Can we change the way for IP assignment?*<br>
Unfortunately, for now, its no way. WSL2 Network service is provided by **Internal Virtual Switch** for Hyper-V. This service would have been able to change the way for IP assignment. But Microsoft deprecated the feature, let the way for IP assignment always is DHCP.<br>
So, the project provides two way to keep static ip for your linux vm.

1. [Dynamic Banding](#DynamicBanding)
2. [DDNS](#DDNS)
---

# Enviroment
- OS: Windows 11 Pro 21H2 (build 22000.434)
- Linux: Ubuntu-20.04 (installed from Microsoft Shore)

# DynamicBanding
## IDEAS
- First step, execute following command in powershell(run as administrator).
```powershell
Get-NetAdapter "vEthernet (WSL)" | Get-NetIPAddress  | Remove-NetIPAddress -Confirm:$False
New-NetIPAddress -IPAddress "192.168.233.1" -PrefixLength 24 -InterfaceAlias "vEthernet (WSL)"
Get-NetNat | Where-Object Name -Eq WSLNat | Remove-NetNat -Confirm:$False
New-NetNat -Name WSLNat -InternalIPInterfaceAddressPrefix "192.168.233.0/24"
```
- Second step, make root needn't password.
```bash
sudo visudo
# Append a line
# youruser ALL=(ALL) NOPASSWD:ALL
```
- Third step, execute following command in linux(root).
```bash
ip addr del $(ip addr show eth0 | grep 'inet\b' | awk '{print $2}' | head -n 1) dev eth0
ip addr add 192.168.233.2/24 broadcast 192.168.233.255 dev eth0
ip route add 0.0.0.0/0 via 192.168.233.1 dev eth0
# WSL always regenerates resolv.conf at ubuntu session restarted
# So, injected .bashrc was used to modify resolv.conf every time
echo "sudo sed -i -r \"s/nameserver .*?/nameserver 192.168.233.1/g\" /etc/resolv.conf" >> ~/.bashrc
```
## AUTO
You can use [WSL2NetworkManager.ps1](DynamicBinding/WSL2NetworkManager.ps1) I have done.<br>
- First step, powershell enable running scripts. By execute following command in powershell(run as administrator).
```powershell
set-ExecutionPolicy RemoteSigned
``` 
- Second step, configure **Task Scheduler**.<br>
**Create Task**: You can name new task according with wishes. then you need to enable **Run with highest privileges** feature, if not, script can't change Windows Network Setting. <br>
Continue, you need add a triggers, which begin the task **at log on**(I suggest you delay task for 10 seconds, you can set it).<br>
Finally, you need add a action which start a program, You can choose location for **WSL2NetworkManager.ps1**. If default executor for ps1 file isn't powershell.exe, you can choose `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`(It's location for powershell.exe on my system, you also can get it by **where** command), and add arguments which choose location for **WSL2NetworkManager.ps1**.
- Third step, copied [WSL2NetworkClient4Ubuntu20.04](DynamicBinding/WSL2NetworkClient4Ubuntu20.04) I have finished to your linux(In principle, the script can used in any newer linux distribution which support bash and ip commands. But I only test it on Ubuntu-20.04). Then you need close root password(see above).
- Fourth step, configure **WSL2NetworkManager.ps1** on code.
```powershell
$LOGGER_FILE = '~\WSL2NetworkManager.log' # or $null if you needn't logging

# CONFIG
$FIXED_GATEWAY = '192.168.233.1'
$FIXED_NAT = '192.168.233.0/24'
$FIXED_BROADCAST = '192.168.233.255'
$FIXED_IP = @{ 
    # Static IP
    'Ubuntu-20.04' = '192.168.233.2'
}

# INTERNAL SCRIPT PATH
$INTERNAL_SCRIPT_PATH = @{
    # Client script path on Ubuntu
    'Ubuntu-20.04' = '/path/to/WSL2NetworkClient'
}
```
Finishe above, you can restart your computer, or run directly the scheduler task to become effective.

# DDNS
## IDEAS
We can startup a service for keeping DNS correct, which modify hosts file dynamically. Then getting real time IP and accessing the service on linux startup. we can pass through local domain to access the VM. In another angle, it's also static.<br>
The way needn't you give up password for root, if you needn't enable sshd automatically.
## AUTO
- First step, installed Python(version>=3.8) to used [wsl2-upgrade-hosts-service.py](DDNS/wsl2-upgrade-hosts-service.py) I have finished. And you may be need install python module aiohttp(version==3.8.1) by pip tool.
- Second step, copied [wsl2ddns](DDNS/wsl2ddns) I have finished to your linux.
- Third step, configure **Task Scheduler**.<br>
**Create Task**: It's used on starting service. You can name new task according with wishes, and enable **Run with highest privileges** feature, if not, service can't edit hosts file.<br>
Then, you need add a triggers, which begin the task **at startup**(I suggest you delay task for little seconds).<br>
Finally, you need add a action which start a program, You should choose location for python installed. And add arguments which is location for **wsl2-upgrade-hosts-service.py**.<br>
**Create another Task**: It's used on notify linux to get newest IP and post it. You also name it according with your wishes.
Then, you need add a triggers, which begin the task **at startup**, you must delay it to service finished startup.<br>
Finally, you need add a action which start a program. You should choose location for wsl(`C:\Users\RealSys\AppData\Local\Microsoft\WindowsApps\wsl.exe` on my computer). And add arguments which is `-d ${Your Linux Distributions} ${location for wsl2ddns on linux}`, like `-d Ubuntu-20.04 ~/wsl2ddns`.
- Fourth step, simply configure.<br>
For **wsl2-upgrade-hosts-service.py**:
```python
WSL2DOMAINS = ['ubuntu.wsl2.local'] # It's domain list that was permitted to modified by service
```
For **wsl2ddns**:
```bash
# domain=${domain you want to use}
curl -s http://$SERV:8448/wsl2ddns?ip=$IPADDR\&domain=ubuntu.wsl2.local >> wsl2ddns.log
```