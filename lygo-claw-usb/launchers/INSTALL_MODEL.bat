@echo off
cd /d "%~dp0.."
title LYGO PUBLIC — Install chat model
echo Pulls a small offline model via Ollama (needs internet once).
echo Default: llama3.2:1b
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\scripts\install_public_model.ps1" %*
echo.
pause
