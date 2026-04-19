[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$VueVersion = "3.5.13",
    [switch]$IfMissingOnly
)

& (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "bootstrap-boardroom.ps1") `
    -Python $Python `
    -VueVersion $VueVersion `
    -IfMissingOnly:$IfMissingOnly
