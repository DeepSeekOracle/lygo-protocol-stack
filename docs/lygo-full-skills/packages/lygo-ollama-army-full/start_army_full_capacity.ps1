# LYGO Ollama Army — OPERATOR-ONLY full-capacity launcher (PowerShell)
# =============================================================================
# NOT the SkillSpector Python skill surface.
# This script deliberately SPAWNS multiple external `python.exe` OS processes.
# Python skill path (ollama_army_launcher / _safe_invoke) = in-process threads + runpy.
# Do NOT claim "no process spawn" for this file.
#
# Prefer safer entrypoints (no OS spawn):
#   python ollama_army_launcher.py --model llama3.2:1b --roles hb-light,draft-simple
#
# Gates required (all three):
#   LYGO_ARMY_FULL_CAPACITY=1
#   LYGO_ARMY_AUTONOMOUS=1
#   LYGO_ARMY_I_CONSENT=1
#   LYGO_STACK_ROOT=<trusted clone>
# Read references/SECURITY.md first.
# =============================================================================
$ErrorActionPreference = "Stop"
$ArmyRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ArmyRoot

if ($env:LYGO_ARMY_FULL_CAPACITY -ne "1") {
    Write-Error @"
Refusing full-capacity start.
This OPERATOR launcher SPAWNS Python OS processes (not in-process threads).
Set LYGO_ARMY_FULL_CAPACITY=1 only after reading references/SECURITY.md
Prefer: python ollama_army_launcher.py  (SkillSpector-safe in-process path)
"@
    exit 1
}
if (-not $env:LYGO_STACK_ROOT) {
    Write-Error "Set LYGO_STACK_ROOT to a trusted lygo-protocol-stack clone before full-capacity mode."
    exit 1
}
if ($env:LYGO_ARMY_AUTONOMOUS -ne "1") {
    Write-Error "Set LYGO_ARMY_AUTONOMOUS=1 to accept long-running autonomous supervisor."
    exit 1
}
if ($env:LYGO_ARMY_I_CONSENT -ne "1") {
    Write-Error @"
Set LYGO_ARMY_I_CONSENT=1 to confirm you accept:
  - OS process spawn of python.exe
  - long-running supervisor loop
  - optional one-shot scripts (self_tune/seed/cron only if LYGO_ARMY_RUN_*=1)
"@
    exit 1
}

Write-Host "=== LYGO Army Full Capacity — OPERATOR SHELL (process spawn) ===" -ForegroundColor Yellow
Write-Host "Stack root: $env:LYGO_STACK_ROOT"
Write-Host "This path uses external python.exe processes. Not the no-spawn Python skill surface." -ForegroundColor Yellow

# Ollama quick check
try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
    Write-Host "[OK] Ollama reachable" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama not ready — deterministic tasks still run; LLM roles wait." -ForegroundColor Yellow
}

# Optional one-shots (each is a separate OS process)
if ($env:LYGO_ARMY_RUN_SELF_TUNE -eq "1") {
    Write-Host "[SPAWN] army_self_tune.py (mutating if self_tune.enabled)" -ForegroundColor DarkYellow
    python -B ollama_command_center\scripts\army_self_tune.py
}
if ($env:LYGO_ARMY_SEED_TASKS -eq "1") {
    Write-Host "[SPAWN] seed_productive_tasks.py" -ForegroundColor DarkYellow
    python -B seed_productive_tasks.py
}
if ($env:LYGO_ARMY_RUN_CRON -eq "1") {
    Write-Host "[SPAWN] army_cron_once.py" -ForegroundColor DarkYellow
    python -B ollama_command_center\scripts\army_cron_once.py
}
if ($env:LYGO_ARMY_VERIFY_TUNE -eq "1") {
    Write-Host "[SPAWN] verify_army_tuning.py" -ForegroundColor DarkYellow
    python -B ollama_command_center\scripts\verify_army_tuning.py
}

Write-Host "[SPAWN] sentinel_heartbeat.py" -ForegroundColor DarkYellow
python -B ollama_command_center\scripts\sentinel_heartbeat.py

Write-Host "Starting autonomous supervisor (SPAWN python — env already gated)..." -ForegroundColor Cyan
python -B ollama_command_center\scripts\army_autonomous_supervisor.py
