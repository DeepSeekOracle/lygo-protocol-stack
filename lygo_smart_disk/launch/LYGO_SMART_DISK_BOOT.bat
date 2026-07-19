@echo off
setlocal
title LYGO SMART DISK AGENT
set "SDA=%~dp0.."
for %%I in ("%SDA%") do set "SDA=%%~fI"
set "LYGO_SMART_DISK_ROOT=%SDA%"
cd /d "%SDA%"

echo ================================================
echo  LYGO SMART DISK AGENT — one-shot boot
echo  Root: %SDA%
echo  Portal: http://localhost:9631/  (local operator token)
echo ================================================

REM Do NOT kill host Ollama (Round-2 fix) — reuse if warm
echo [1/3] Probing Ollama on localhost:11434...
curl -s -m 2 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo      Ollama not responding. Start host Ollama or portable USB Ollama.
  echo      Preferred models: qwen2.5:3b  or  llama3.2:1b
) else (
  echo      Ollama warm.
)

echo [2/3] Ensuring local operator token...
python -u "%SDA%\agent\smart_disk_agent.py" token
echo      Token file: %SDA%\data\.sda_local_token

echo [3/3] Starting Smart Disk supervisor (browser gets ?t= token once)...
start "LYGO SMART DISK AGENT" python -u "%SDA%\agent\smart_disk_agent.py" serve

echo.
echo Auth: local token required on HTTP (not a cloud password).
echo CLI memory: python agent\smart_disk_agent.py limb memory
echo Stop:  launch\LYGO_SMART_DISK_STOP.bat
endlocal
