@echo off
setlocal EnableExtensions
title LYGO LLM Console
set "ROOT=%~dp0"
if defined LYGO_CONSOLE_ROOT set "ROOT=%LYGO_CONSOLE_ROOT%"
cd /d "%ROOT%"
echo.
echo  LYGO Agent Portal — local console
echo  %CD%
echo.
if not exist "%ROOT%workspace\SOUL.md" (
  echo  First run: seeding public identity...
  where py >nul 2>&1 && (py -3 -u "%ROOT%src\install.py") || (python -u "%ROOT%src\install.py")
)
for %%P in (9641 11441 11442) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
    echo  Stopping old PID %%A on %%P
    taskkill /F /PID %%A >nul 2>&1
  )
)
if exist "C:\Python313\python.exe" (set "LYGO_PYTHON=C:\Python313\python.exe") else (
  where py >nul 2>&1 && (set "LYGO_PYTHON=py") || (set "LYGO_PYTHON=python")
)
echo  Starting http://127.0.0.1:9641/
echo.
"%LYGO_PYTHON%" -u "%ROOT%src\server.py" serve
echo.
echo  Console stopped.
pause
