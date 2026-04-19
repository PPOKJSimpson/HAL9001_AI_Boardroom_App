[CmdletBinding()]
param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8765,
    [string]$Python = "python",
    [switch]$Resume
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $RepoRoot ".venv\\Scripts\\python.exe"
$BackendMain = Join-Path $RepoRoot "backend\\main.py"
$CurrentSessionPointer = Join-Path $RepoRoot ".ai-boardroom\\current-session.json"

if (Test-Path -LiteralPath $VenvPython) {
    $PythonExe = $VenvPython
}
else {
    Write-Warning ".venv was not found. Falling back to '$Python'."
    $PythonExe = $Python
}

if (-not (Test-Path -LiteralPath $BackendMain)) {
    throw "Missing backend entrypoint: $BackendMain. The backend slice must exist before start-boardroom.ps1 can launch the app."
}

if (-not $Resume) {
    Remove-Item -LiteralPath $CurrentSessionPointer -Force -ErrorAction SilentlyContinue
}

Write-Host "Starting AI Boardroom on http://$ListenHost`:$Port"
Set-Location $RepoRoot
& $PythonExe -m uvicorn backend.main:app --host $ListenHost --port $Port
