[CmdletBinding()]
param(
    [string]$Distribution = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'

$keeper = Get-CimInstance Win32_Process -Filter "Name = 'wsl.exe'" |
    Where-Object { $_.CommandLine -match 'SQLBot-adaptive/dev/postgres/keepalive\.sh' }

if ($keeper) {
    & wsl.exe -d $Distribution -- bash -lc 'sudo pg_ctlcluster 17 main stop' 2>$null | Out-Null
    $keeper | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Write-Output 'SQLBot development database stopped.'
} else {
    Write-Output 'SQLBot development database keeper is not running.'
}
