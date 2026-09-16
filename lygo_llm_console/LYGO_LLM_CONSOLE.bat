@echo off
setlocal EnableExtensions
title LYGO LLM Console v1.1
set CANON=I:\E Drive\lygo-protocol-stack\lygo_llm_console
cd /d "%CANON%"
echo.
echo  LYGO Agent Portal v1.1
echo  Folder: %CANON%
echo  Page:   http://127.0.0.1:9641/
echo.
REM netstat (not Get-NetTCPConnection — that hangs on this PC)
for %%P in (9641 11441 11442) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
    echo  Stopping PID %%A on port %%P
    taskkill /F /PID %%A >nul 2>&1
  )
)
if exist "C:\Python313\python.exe" (set "LYGO_PYTHON=C:\Python313\python.exe") else (set "LYGO_PYTHON=py")
if defined LYGO_PYTHON if exist "%LYGO_PYTHON%" goto :run
set "LYGO_PYTHON=py"
:run
echo  Python: %LYGO_PYTHON%
echo  Starting server...
echo.
"%LYGO_PYTHON%" -u "%CANON%\src\server.py" serve %*
echo.
echo  Console exited. Code %ERRORLEVEL%
pause
