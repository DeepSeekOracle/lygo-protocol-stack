# Install LYGO Ollama desktop launchers (operator convenience)
#
# Requires: LYGO_ARMY_INSTALL_DESKTOP=1
# Read references/SECURITY.md first.
#
# Army launcher does NOT inject consent env vars. You must set
# LYGO_ARMY_AUTONOMOUS=1 and LYGO_ARMY_I_CONSENT=1 yourself before starting
# (or the bat exits 1). Prefer: python ollama_army_launcher.py

$ErrorActionPreference = "Stop"
if ($env:LYGO_ARMY_INSTALL_DESKTOP -ne "1") {
    Write-Error "Refusing desktop installers. Set LYGO_ARMY_INSTALL_DESKTOP=1 after reading SECURITY.md"
    exit 1
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$ArmyRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Scripts = Join-Path $ArmyRoot "ollama_command_center\scripts"
$Stack = if ($env:LYGO_STACK_ROOT) { $env:LYGO_STACK_ROOT } else { "D:\lygo-protocol-stack" }

Write-Host "About to write launchers to: $Desktop"
Write-Host "  - Heartbeats: sentinel only (no dual consent)"
Write-Host "  - Army: REFUSES unless you already set LYGO_ARMY_AUTONOMOUS=1 and LYGO_ARMY_I_CONSENT=1"
Write-Host "Confirm by re-running with LYGO_ARMY_INSTALL_DESKTOP=1 only after reading SECURITY.md."

$HeartbeatsBat = @"
@echo off
title LYGO Ollama Heartbeats (sentinel only)
cd /d "$Scripts"
set LYGO_STACK_ROOT=$Stack
echo Sentinel loop only. Close window to stop.
echo Does NOT set autonomous consent.
python heartbeats_only.py
pause
"@

$ArmyBat = @"
@echo off
title LYGO Ollama Army (requires external dual consent)
cd /d "$Scripts"
set LYGO_STACK_ROOT=$Stack
if not "%LYGO_ARMY_AUTONOMOUS%"=="1" (
  echo REFUSE: set LYGO_ARMY_AUTONOMOUS=1 in this shell first
  echo Prefer safer: python ollama_army_launcher.py
  pause
  exit /b 1
)
if not "%LYGO_ARMY_I_CONSENT%"=="1" (
  echo REFUSE: set LYGO_ARMY_I_CONSENT=1 in this shell first
  echo This launcher does NOT inject consent for you.
  pause
  exit /b 1
)
echo Dual consent env already set by operator — starting supervisor.
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
Write-Host "WARNING: Army .bat does not auto-set consent. Set env in shell before double-click will still fail — use a pre-consented shell or set User env vars deliberately."
