[CmdletBinding()]
param(
    [string]$Distribution = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$keepaliveWindowsPath = Join-Path $repoRoot 'dev\postgres\keepalive.sh'
if (-not (Test-Path -LiteralPath $keepaliveWindowsPath)) {
    throw "Missing WSL keep-alive script: $keepaliveWindowsPath"
}

$driveName = [System.IO.Path]::GetPathRoot($repoRoot).TrimEnd('\').TrimEnd(':').ToLowerInvariant()
$relativePath = $keepaliveWindowsPath.Substring([System.IO.Path]::GetPathRoot($repoRoot).Length).Replace('\', '/')
$keepaliveWslPath = "/mnt/$driveName/$relativePath"
$processMarker = 'SQLBot-adaptive/dev/postgres/keepalive.sh'

function Get-WslAddress {
    param([string]$TargetDistribution)

    if ($TargetDistribution -notmatch '^[A-Za-z0-9._-]+$') {
        throw 'The WSL distribution name contains unsupported characters.'
    }

    # WSL can emit a non-fatal networking warning on stderr. PowerShell turns
    # that warning into a terminating NativeCommandError when Stop is enabled,
    # so capture both streams and decide from the real process exit code.
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = 'wsl.exe'
    $startInfo.Arguments = "-d $TargetDistribution --exec hostname -I"
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::Start($startInfo)
    $process.WaitForExit()
    $stdout = $process.StandardOutput.ReadToEnd()
    if ($process.ExitCode -ne 0) {
        # WSL may need another iteration while a new distribution process is
        # starting; the caller already retries with a bounded loop.
        return ''
    }
    return $stdout
}

$keeper = Get-CimInstance Win32_Process -Filter "Name = 'wsl.exe'" |
    Where-Object { $_.CommandLine -match [regex]::Escape($processMarker) } |
    Select-Object -First 1

if (-not $keeper) {
    $arguments = @('-d', $Distribution, '--exec', 'bash', $keepaliveWslPath)
    $keeperProcess = Start-Process -FilePath 'wsl.exe' -ArgumentList $arguments -WindowStyle Hidden -PassThru
    Write-Host "Started SQLBot development database keeper (PID $($keeperProcess.Id))."
}

$databaseIp = $null
for ($attempt = 1; $attempt -le 10; $attempt++) {
    $rawIp = Get-WslAddress -TargetDistribution $Distribution
    $cleanIp = (($rawIp -replace [char]0, '').Trim() -split '\s+')[0]
    if ($cleanIp -and (Test-NetConnection -ComputerName $cleanIp -Port 5432 -InformationLevel Quiet)) {
        $databaseIp = $cleanIp
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $databaseIp) {
    throw 'PostgreSQL did not become reachable on WSL port 5432.'
}

Write-Host "PostgreSQL is reachable at ${databaseIp}:5432."
Write-Output $databaseIp
