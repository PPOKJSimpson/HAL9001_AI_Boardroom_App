[CmdletBinding()]
param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8765,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $RepoRoot ".venv\\Scripts\\python.exe"
$BackendMain = Join-Path $RepoRoot "backend\\main.py"

if (Test-Path -LiteralPath $VenvPython) {
    $PythonExe = $VenvPython
}
else {
    Write-Warning ".venv was not found. Falling back to '$Python'."
    $PythonExe = $Python
}

if (-not (Test-Path -LiteralPath $BackendMain)) {
    throw "Missing backend entrypoint: $BackendMain. The backend slice must exist before run.ps1 can launch the app."
}

Write-Host "Starting AI Boardroom on http://$ListenHost`:$Port"
Set-Location $RepoRoot
& $PythonExe -m uvicorn backend.main:app --host $ListenHost --port $Port
