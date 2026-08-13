# OPTIONAL steward desktop launcher: Genesis + LYRA ops (Discord/crypto live outside this skill).
# NOT required for LYGO Ollama Army core.
# Scope: operator steward machine only. Requires LYGO_ARMY_INSTALL_STEWARD_DESKTOP=1.
#
# This does NOT install Discord tokens or wallets into the army skill package.

$ErrorActionPreference = "Stop"
if ($env:LYGO_ARMY_INSTALL_STEWARD_DESKTOP -ne "1") {
    Write-Error @"
Refusing steward desktop installer (Discord/crypto bridge).
This is OUT OF SCOPE for the default Ollama army skill.
Set LYGO_ARMY_INSTALL_STEWARD_DESKTOP=1 only on a trusted steward PC.
"@
    exit 1
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$LyraCore = if ($env:LYRA_CORE_ROOT) { $env:LYRA_CORE_ROOT } else { "I:\E Drive\LYRA_CORE" }
$Genesis = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "genesis_console"

if (-not (Test-Path (Join-Path $LyraCore "lygo_lightfather_ops_launcher.py"))) {
    Write-Error "Missing steward launcher under LYRA_CORE — aborting (no silent fallback)."
    exit 1
}

$Bat = @"
@echo off
title LYGO Steward Ops (optional - not army core)
cd /d "$LyraCore"
set LYGO_STACK_ROOT=$env:LYGO_STACK_ROOT
echo OPTIONAL steward path: Genesis + Discord limb outside army skill package.
echo Tokens/wallets must already exist in LYRA_CORE env — never shipped in army skill.
python -B lygo_lightfather_ops_launcher.py
pause
"@

$path = Join-Path $Desktop "LYGO Steward Ops (Optional).bat"
Set-Content -Path $path -Value $Bat -Encoding ASCII
Write-Host "Created: $path"
Write-Host "Genesis-only: run install_genesis_desktop.ps1 separately."
