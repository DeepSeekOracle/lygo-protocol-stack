# LYGO Ollama Army — full capacity v3 (network-builder + mesh-cartographer)
$ErrorActionPreference = "Stop"
$ArmyRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ArmyRoot
if ($env:LYGO_ARMY_FULL_CAPACITY -ne "1") {
    Write-Error "Refusing full-capacity start. Set LYGO_ARMY_FULL_CAPACITY=1 after reading references/SECURITY.md"
    exit 1
}
if (-not $env:LYGO_STACK_ROOT) {
    Write-Error "Set LYGO_STACK_ROOT to your lygo-protocol-stack clone before full-capacity mode."
    exit 1
}

Write-Host "=== LYGO Army Full Capacity v3 ===" -ForegroundColor Cyan
Write-Host "Stack root: $env:LYGO_STACK_ROOT"

# Ollama quick check
try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
    Write-Host "[OK] Ollama reachable" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama not ready — deterministic tasks still run; LLM roles wait." -ForegroundColor Yellow
}

python -B ollama_command_center\scripts\army_self_tune.py
python -B seed_productive_tasks.py
python -B ollama_command_center\scripts\army_cron_once.py
python -B ollama_command_center\scripts\verify_army_tuning.py
python -B ollama_command_center\scripts\sentinel_heartbeat.py

Write-Host "Starting autonomous supervisor (daemons + sentinel loop + hourly cron)..." -ForegroundColor Cyan
python -B ollama_command_center\scripts\army_autonomous_supervisor.py