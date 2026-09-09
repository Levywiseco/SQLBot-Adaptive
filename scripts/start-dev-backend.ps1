[CmdletBinding()]
param(
    [string]$Distribution = 'Ubuntu',
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$databaseIp = (& (Join-Path $PSScriptRoot 'start-dev-database.ps1') -Distribution $Distribution |
    Select-Object -Last 1).Trim()
$pythonPath = Join-Path $repoRoot 'backend\.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Backend environment is missing. Run uv sync --extra cpu from the backend directory.'
}

$env:POSTGRES_SERVER = $databaseIp
Set-Location (Join-Path $repoRoot 'backend')
& $pythonPath -m uvicorn main:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
