# LYGO Army Idle Guardian — desktop launcher (safe offline housekeeping)
$ErrorActionPreference = "Stop"
$Desktop = [Environment]::GetFolderPath("Desktop")

$ArmyRoot = if (Test-Path "$PSScriptRoot") {
    "$PSScriptRoot"
} else {
    $PSScriptRoot
}
$Scripts = Join-Path $ArmyRoot "ollama_command_center\scripts"
$Stack = "%LYGO_STACK_ROOT%"
$Lyra = "%LYRA_CORE_ROOT%"

$Bat = @"
@echo off
title LYGO Army Idle Guardian
cd /d "$Scripts"
set LYGO_ARMY_IDLE_GUARDIAN=1
set LYGO_STACK_ROOT=$Stack
set LYRA_CORE_ROOT=$Lyra
set LYGO_AUTHORITY_ROOT=I:\E Drive
echo.
echo  LYGO Idle Guardian — housekeeping only (no social, no push).
echo  Journal: ollama_command_center\workspace\idle_guardian_journal.jsonl
echo  Upgrades: ollama_command_center\workspace\idle_upgrade_findings.jsonl
echo  Close this window to stop.
echo.
python army_idle_guardian_supervisor.py
pause
"@

$path = Join-Path $Desktop "LYGO Army Idle Guardian.bat"
Set-Content -Path $path -Value $Bat -Encoding ASCII
Write-Host "Created: $path"
Write-Host "Docs: $ArmyRoot\ollama_command_center\IDLE_GUARDIAN.md"
