@echo off
setlocal EnableExtensions
title LYGO LLM Console — public install
cd /d "%~dp0"
echo.
echo  LYGO LLM Console — public install
echo  This folder: %CD%
echo  Seeds Soul / Identity / Memory for YOU. Does not copy steward vaults.
echo.
where py >nul 2>&1 && (set "LYGO_PYTHON=py -3") || (set "LYGO_PYTHON=python")
%LYGO_PYTHON% -u "%~dp0src\install.py" %*
if errorlevel 1 (
  echo.
  echo  Install needs Python 3. https://www.python.org/downloads/
  pause
  exit /b 1
)
echo.
echo  Optional engine download (ggml-org llama-server CPU zip):
choice /C YN /M "Fetch llama-server into engine now"
if errorlevel 2 goto done
if errorlevel 1 %LYGO_PYTHON% -u "%~dp0src\install.py" --fetch-engine
:done
echo.
echo  Start the console with LYGO_LLM_CONSOLE.bat
pause
