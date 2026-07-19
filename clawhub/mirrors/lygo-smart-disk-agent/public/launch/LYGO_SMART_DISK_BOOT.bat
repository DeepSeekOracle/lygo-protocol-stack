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
echo  Portal: http://127.0.0.1:9631/  (no password)
echo ================================================

REM Do NOT kill host Ollama (Round-2 fix) — reuse if warm
echo [1/3] Probing Ollama on 127.0.0.1:11434...
curl -s -m 2 http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo      Ollama not responding. Start host Ollama or portable USB Ollama.
  echo      Preferred models: qwen2.5:3b  or  llama3.2:1b
) else (
  echo      Ollama warm.
)

echo [2/3] Starting Smart Disk supervisor...
start "LYGO SMART DISK AGENT" /MIN python -u "%SDA%\agent\smart_disk_agent.py" serve

echo [3/3] Browser opens automatically from agent (loopback).
echo.
echo Limbs: help status health lattice memory army-sentinel chat
echo Stop:  launch\LYGO_SMART_DISK_STOP.bat
endlocal
