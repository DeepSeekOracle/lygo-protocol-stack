# LYGO Lightfather Ops — Genesis + Discord + crypto dashboard
$Desktop = [Environment]::GetFolderPath("Desktop")
$LyraCore = "I:\E Drive\LYRA_CORE"
$Genesis = "I:\E Drive\.grok\skills\lygo-ollama-army\genesis_console"

$Bat = @"
@echo off
title LYGO Lightfather Ops
cd /d "$LyraCore"
set LYGO_STACK_ROOT=I:\E Drive\lygo-protocol-stack
echo Starting Genesis Console + Discord Ollama limb...
python -B lygo_lightfather_ops_launcher.py
pause
"@

$path = Join-Path $Desktop "LYGO Lightfather Ops.bat"
Set-Content -Path $path -Value $Bat -Encoding ASCII
Write-Host "Created: $path"

# Refresh genesis-only shortcut too
& "$PSScriptRoot\install_genesis_desktop.ps1"