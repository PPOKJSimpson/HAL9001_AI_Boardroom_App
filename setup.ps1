[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$VueVersion = "3.5.13"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $RepoRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\\python.exe"
$RequirementsPath = Join-Path $RepoRoot "requirements.txt"
$VendorDir = Join-Path $RepoRoot "frontend\\vendor"
$VendorVuePath = Join-Path $VendorDir "vue.esm-browser.prod.js"
$VueUrl = "https://unpkg.com/vue@$VueVersion/dist/vue.esm-browser.prod.js"

Write-Host "AI Boardroom setup starting..."

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "Creating virtual environment at $VenvDir"
    & $Python -m venv $VenvDir
}
else {
    Write-Host "Using existing virtual environment at $VenvDir"
}

Write-Host "Upgrading pip"
& $VenvPython -m pip install --upgrade pip

if (Test-Path -LiteralPath $RequirementsPath) {
    Write-Host "Installing dependencies from requirements.txt"
    & $VenvPython -m pip install -r $RequirementsPath
}
else {
    Write-Warning "requirements.txt not found. Skipping dependency install for now."
}

Write-Host "Checking for Playwright"
& $VenvPython -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('playwright') else 1)"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Installing Playwright Chromium"
    & $VenvPython -m playwright install chromium
}
else {
    Write-Warning "Playwright is not installed in the venv. Skipping browser install."
}

if (-not (Test-Path -LiteralPath $VendorDir)) {
    New-Item -ItemType Directory -Path $VendorDir | Out-Null
}

Write-Host "Vendoring Vue runtime from $VueUrl"
Invoke-WebRequest -Uri $VueUrl -OutFile $VendorVuePath

Write-Host "Setup complete."
