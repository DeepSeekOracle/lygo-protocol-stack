# LYGO Genesis Console — Desktop launcher
$Desktop = [Environment]::GetFolderPath("Desktop")
$Genesis = "$PSScriptRoot\genesis_console"

$Bat = @"
@echo off
title LYGO Lightfather Genesis Console
cd /d "$Genesis"
set LYGO_STACK_ROOT=%LYGO_STACK_ROOT%
set LYGO_GENESIS_PORT=9963
set LYGO_GENESIS_REFRESH=120
echo Starting Genesis Console v3 (full LYGO monitor) on http://127.0.0.1:9963/
echo Close this window to stop the dashboard server.
python server.py
pause
"@

$path = Join-Path $Desktop "LYGO Genesis Console.bat"
Set-Content -Path $path -Value $Bat -Encoding ASCII
Write-Host "Created: $path"
