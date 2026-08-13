# LYGO Army Idle Guardian — desktop launcher
# Requires: LYGO_ARMY_INSTALL_DESKTOP=1
# Also requires LYGO_ARMY_IDLE_GUARDIAN=1 at run time (not injected).

$ErrorActionPreference = "Stop"
if ($env:LYGO_ARMY_INSTALL_DESKTOP -ne "1") {
    Write-Error "Refusing desktop installer. Set LYGO_ARMY_INSTALL_DESKTOP=1 after reading SECURITY.md"
    exit 1
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$ArmyRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Scripts = Join-Path $ArmyRoot "ollama_command_center\scripts"
$Stack = if ($env:LYGO_STACK_ROOT) { $env:LYGO_STACK_ROOT } else { "" }

$Bat = @"
@echo off
title LYGO Army Idle Guardian
cd /d "$Scripts"
if not "%LYGO_ARMY_IDLE_GUARDIAN%"=="1" (
  echo REFUSE: set LYGO_ARMY_IDLE_GUARDIAN=1 in this shell first
  echo This launcher does NOT inject the idle guardian gate.
  pause
  exit /b 1
)
if not "$Stack"=="" set LYGO_STACK_ROOT=$Stack
echo Idle Guardian — housekeeping roles from idle_guardian.roles only
echo Planting/social OFF unless config allows.
python army_idle_guardian_supervisor.py
pause
"@

$path = Join-Path $Desktop "LYGO Army Idle Guardian.bat"
Set-Content -Path $path -Value $Bat -Encoding ASCII
Write-Host "Created: $path"
Write-Host "Docs: $ArmyRoot\ollama_command_center\IDLE_GUARDIAN.md"
