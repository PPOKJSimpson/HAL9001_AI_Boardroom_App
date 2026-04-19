[CmdletBinding()]
param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8765,
    [string]$Python = "python"
)

& (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "start-boardroom.ps1") `
    -ListenHost $ListenHost `
    -Port $Port `
    -Python $Python
