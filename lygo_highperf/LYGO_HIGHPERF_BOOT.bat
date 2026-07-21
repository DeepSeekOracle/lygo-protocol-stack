@echo off
title LYGO HIGH-PERF — Uncensored Qwen (llama.cpp)
cd /d D:\LYGO_HIGHPERF
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\01_stage_models.ps1"
if not exist "%~dp0bin\llama-server.exe" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\02_download_llama_server.ps1"
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\03_boot_llamacpp.ps1"
pause
