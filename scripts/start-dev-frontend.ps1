[CmdletBinding()]
param(
    [int]$Port = 5173
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$frontendPath = Join-Path $repoRoot 'frontend'
if (-not (Test-Path -LiteralPath (Join-Path $frontendPath 'node_modules'))) {
    throw 'Frontend dependencies are missing. Run npm install from the frontend directory.'
}

Set-Location $frontendPath
npm exec vite -- --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
