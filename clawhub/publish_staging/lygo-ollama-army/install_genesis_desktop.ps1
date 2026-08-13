# LYGO Genesis Console — Desktop launcher
# Requires: LYGO_ARMY_INSTALL_DESKTOP=1
# Does not set autonomous/consent flags. Localhost dashboard only.

$ErrorActionPreference = "Stop"
if ($env:LYGO_ARMY_INSTALL_DESKTOP -ne "1") {
    Write-Error "Refusing desktop installer. Set LYGO_ARMY_INSTALL_DESKTOP=1 after reading SECURITY.md"
    exit 1
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$Genesis = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "genesis_console"
if (-not (Test-Path $Genesis)) {
    Write-Error "genesis_console not found next to installer"
    exit 1
}
$Stack = if ($env:LYGO_STACK_ROOT) { $env:LYGO_STACK_ROOT } else { "" }

$Bat = @"
@echo off
title LYGO Genesis Console (localhost only)
cd /d "$Genesis"
if not "$Stack"=="" set LYGO_STACK_ROOT=$Stack
set LYGO_GENESIS_PORT=9963
set LYGO_GENESIS_REFRESH=120
echo Genesis Console on http://127.0.0.1:9963/ (local only)
echo Public probes OFF unless LYGO_GENESIS_PROBE_PUBLIC=1
echo Close this window to stop.
python server.py
pause
"@

$path = Join-Path $Desktop "LYGO Genesis Console.bat"
Set-Content -Path $path -Value $Bat -Encoding ASCII
Write-Host "Created: $path (requires LYGO_ARMY_INSTALL_DESKTOP=1 to re-install)"
