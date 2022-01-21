# Fixed Gateway     in 192.168.233.1
#       Broadcast   in 192.168.233.255

$WSL2_ETHERNET = 'vEthernet (WSL)'
$LOGGER_FILE = '~\WSL2NetworkManager.log' # or $null if you needn't logging

# CONFIG
$FIXED_GATEWAY = '192.168.233.1'
$FIXED_NAT = '192.168.233.0/24'
$FIXED_BROADCAST = '192.168.233.255'
$FIXED_IP = @{ 
    'Ubuntu-20.04' = '192.168.233.2'
}

# INTERNAL SCRIPT PATH
$INTERNAL_SCRIPT_PATH = @{
    'Ubuntu-20.04' = '/path/to/WSL2NetworkClient'
}

function Logger($info) {
    Write-Output $info 2>&1 >> $LOGGER_FILE
}

# MAIN
Logger "<Executor in $(Get-date)>"

# Power on client
foreach ($Key in $FIXED_IP.Keys) {
    wsl -u root -d $Key echo $Key up 2>&1 >> $LOGGER_FILE
}

# Upgrade gateway
$CURRENT_GATEWAY = $(Get-NetAdapter $WSL2_ETHERNET | Get-NetIPAddress)
If ($CURRENT_GATEWAY.IPv4Address -ne $FIXED_GATEWAY) {
    # Check if gateway changed 
    # If changed, reset wsl2 ethernet configure
    $CURRENT_GATEWAY | Remove-NetIPAddress -Confirm:$False
    New-NetIPAddress -IPAddress $FIXED_GATEWAY -PrefixLength 24 -InterfaceAlias $WSL2_ETHERNET
    Get-NetNat | Where-Object Name -Eq WSLNat | Remove-NetNat -Confirm:$False
    New-NetNat -Name WSLNat -InternalIPInterfaceAddressPrefix $FIXED_NAT
    Logger "Gateway upgraded."
} Else {
    Logger "Gateway needn't upgrading."
}

# Notify client upgrade
foreach ($Key in $FIXED_IP.Keys) {
    if ($INTERNAL_SCRIPT_PATH.ContainsKey($Key)) {
        Logger "[Executing $Key Client Script]"
        $Path = $INTERNAL_SCRIPT_PATH[$Key]
        $cmd = -Join("wsl -u root -d ", $Key, " $Path ", $FIXED_IP[$Key], " $FIXED_GATEWAY $FIXED_BROADCAST")
        powershell -command $cmd 2>&1 >> $LOGGER_FILE
    }
}

Logger ""