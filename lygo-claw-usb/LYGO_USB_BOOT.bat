@echo off
setlocal EnableExtensions
title LYGO CLAW PUBLIC — Offline Agent Dashboard
cd /d "%~dp0"

echo ================================================================
echo  LYGO CLAW PUBLIC USB  —  Offline agent chat dashboard
echo  Root: %CD%
echo  No password. No models in git — install once then go offline.
echo ================================================================
echo.

set "LYGO_BUILDER_KEY_ROOT=%CD%"
set "OLLAMA_HOST=127.0.0.1:11434"
if exist "%CD%\product\models\ollama\blobs" (
  set "OLLAMA_MODELS=%CD%\product\models\ollama"
) else (
  set "OLLAMA_MODELS=%CD%\product\models\ollama"
)
set "OLLAMA_ORIGINS=*,http://127.0.0.1,http://localhost,http://127.0.0.1:9631,http://localhost:9631"
set "OLLAMA_KEEP_ALIVE=30m"
set "LYGO_AGENT_PORT=9631"

REM Optional live lattice (not required for chat)
if exist "D:\lygo-protocol-stack\docs" (
  set "LYGO_STACK_ROOT=D:\lygo-protocol-stack"
) else if exist "%CD%\stack\lygo-protocol-stack\docs" (
  set "LYGO_STACK_ROOT=%CD%\stack\lygo-protocol-stack"
)

echo [1/3] Environment...
if exist "scripts\bootstrap_env.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\bootstrap_env.ps1"
)

echo [2/3] Ollama serve...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\ensure_ollama_serve.ps1"
if errorlevel 1 (
  echo.
  echo Ollama not ready. First-time public setup:
  echo   1. Install Ollama: https://ollama.com/download
  echo   2. scripts\install_public_model.ps1
  echo   3. Re-run this boot.
  echo.
  pause
  exit /b 1
)

echo [3/3] Agent dashboard :9631 ...
where python >nul 2>&1
if errorlevel 1 (
  echo Python 3.11+ required on PATH. https://www.python.org/downloads/
  pause
  exit /b 1
)

start "LYGO Agent Server" /MIN cmd /c "cd /d "%CD%" && set LYGO_BUILDER_KEY_ROOT=%CD%&& set OLLAMA_MODELS=%OLLAMA_MODELS%&& set OLLAMA_HOST=%OLLAMA_HOST%&& set LYGO_STACK_ROOT=%LYGO_STACK_ROOT%&& python scripts\lygo_usb_agent_server.py"

echo Waiting for agent UI...
set /a _n=0
:wait_agent
set /a _n+=1
powershell -NoProfile -Command "try { Invoke-RestMethod 'http://127.0.0.1:9631/api/status' -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }"
if not errorlevel 1 goto :open_ui
if %_n% GEQ 20 goto :open_ui
timeout /t 1 /nobreak >nul
goto :wait_agent

:open_ui
start "" "http://127.0.0.1:9631/"

echo.
echo ================================================================
echo  READY — type in the browser to talk to the agent
echo    Agent UI:  http://127.0.0.1:9631/
echo    Status:    http://127.0.0.1:9631/api/status
echo    Ollama:    http://127.0.0.1:11434
echo    Models:    %OLLAMA_MODELS%
echo ================================================================
echo.
echo Leave this window open while chatting.
pause
endlocal
