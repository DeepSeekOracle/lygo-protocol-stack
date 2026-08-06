# Install LYGO Ollama desktop launchers (operator convenience)
# WARNING: Desktop army launcher requires dual consent env in the .bat.
# Prefer: python ollama_army_launcher.py (in-process SkillSpector path)
#
# Requires: LYGO_ARMY_INSTALL_DESKTOP=1
# Read references/SECURITY.md first.

$ErrorActionPreference = "Stop"
if ($env:LYGO_ARMY_INSTALL_DESKTOP -ne "1") {
    Write-Error "Refusing desktop installers. Set LYGO_ARMY_INSTALL_DESKTOP=1 after reading SECURITY.md"
    exit 1
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$ArmyRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Scripts = Join-Path $ArmyRoot "ollama_command_center\scripts"
$Stack = if ($env:LYGO_STACK_ROOT) { $env:LYGO_STACK_ROOT } else { "D:\lygo-protocol-stack" }

$HeartbeatsBat = @"
@echo off
title LYGO Ollama Heartbeats (sentinel only)
cd /d "$Scripts"
set LYGO_STACK_ROOT=$Stack
echo Sentinel loop only. Close window to stop.
python heartbeats_only.py
pause
"@

$ArmyBat = @"
@echo off
title LYGO Ollama Army (Autonomous - dual consent required)
cd /d "$Scripts"
set LYGO_STACK_ROOT=$Stack
set LYGO_ARMY_AUTONOMOUS=1
set LYGO_ARMY_I_CONSENT=1
echo WARNING: long-running autonomous supervisor (in-process threads).
echo Dual consent env set in this launcher intentionally.
echo Prefer safer: python ollama_army_launcher.py
python army_autonomous_supervisor.py
pause
"@

$hbPath = Join-Path $Desktop "LYGO Ollama Heartbeats.bat"
$armyPath = Join-Path $Desktop "LYGO Ollama Army (Consent).bat"
Set-Content -Path $hbPath -Value $HeartbeatsBat -Encoding ASCII
Set-Content -Path $armyPath -Value $ArmyBat -Encoding ASCII

Write-Host "Created:"
Write-Host "  $hbPath"
Write-Host "  $armyPath"
Write-Host "Army launcher embeds dual consent env; review before double-click."
