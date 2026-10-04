@echo off
cd /d "%~dp0.."
title LYGO PUBLIC — System check
echo Root: %CD%
echo.
where python >nul 2>&1 && (echo [OK] python) || (echo [MISSING] python 3.11+ — https://www.python.org/downloads/)
where ollama >nul 2>&1 && (echo [OK] ollama on PATH) || (
  if exist "%CD%\product\runtime\ollama\ollama.exe" (echo [OK] portable ollama.exe) else (echo [MISSING] ollama — https://ollama.com/download)
)
if exist "%CD%\scripts\lygo_usb_agent_server.py" (echo [OK] agent server) else (echo [MISSING] agent server)
if exist "%CD%\dashboard\agent-ui\index.html" (echo [OK] agent UI) else (echo [MISSING] agent UI)
if exist "%CD%\product\models\ollama\blobs" (echo [OK] models folder has blobs) else (echo [NOTE] no model yet — run launchers\INSTALL_MODEL.bat)
echo.
powershell -NoProfile -Command "try { $t=Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2; Write-Host ('[OK] Ollama up — ' + @($t.models).Count + ' model(s)') } catch { Write-Host '[ ] Ollama not running (boot will start it)' }"
echo.
pause
