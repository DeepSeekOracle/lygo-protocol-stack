@echo off
title LYGO SMART DISK AGENT — stop
echo Stopping Smart Disk agent windows titled LYGO SMART DISK AGENT...
taskkill /FI "WINDOWTITLE eq LYGO SMART DISK AGENT*" /F >nul 2>&1
echo Done. (Host Ollama left running.)
