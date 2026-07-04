# Install LYGO Ollama desktop launchers (Heartbeats + Full Army)
$Desktop = [Environment]::GetFolderPath("Desktop")
$ArmyRoot = "I:\E Drive\.grok\skills\lygo-ollama-army"
$Scripts = "$ArmyRoot\ollama_command_center\scripts"

$HeartbeatsBat = @"
@echo off
title LYGO Ollama Heartbeats
cd /d "$Scripts"
set LYGO_STACK_ROOT=I:\E Drive\lygo-protocol-stack
echo LYGO Heartbeats ONLY - sentinel every 5 min. Close window to stop.
python heartbeats_only.py
pause
"@

$ArmyBat = @"
@echo off
title LYGO Ollama Army (Autonomous)
cd /d "$Scripts"
set LYGO_STACK_ROOT=I:\E Drive\lygo-protocol-stack
echo LYGO Full Army - supervisor + queue daemon. Close window to stop.
python army_autonomous_supervisor.py
pause
"@

$hbPath = Join-Path $Desktop "LYGO Ollama Heartbeats.bat"
$armyPath = Join-Path $Desktop "LYGO Ollama Army.bat"
Set-Content -Path $hbPath -Value $HeartbeatsBat -Encoding ASCII
Set-Content -Path $armyPath -Value $ArmyBat -Encoding ASCII
$GenesisInstaller = Join-Path $ArmyRoot "install_genesis_desktop.ps1"
if (Test-Path $GenesisInstaller) {
    & $GenesisInstaller
}

$IdleInstaller = Join-Path $ArmyRoot "install_idle_guardian_desktop.ps1"
if (Test-Path $IdleInstaller) {
    & $IdleInstaller
}

Write-Host "Created:"
Write-Host "  $hbPath"
Write-Host "  $armyPath"