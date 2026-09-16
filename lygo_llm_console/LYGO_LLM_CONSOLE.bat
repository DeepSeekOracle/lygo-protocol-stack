@echo off
setlocal
title LYGO LLM Console v1.1
REM Always the NEW console (not kit/ or public/ copies)
set CANON=I:\E Drive\lygo-protocol-stack\lygo_llm_console
cd /d "%CANON%"
echo.
echo  LYGO Agent Portal v1.1  —  24 limbs, Scan/Boot in HEADER
echo  Folder: %CANON%
echo  Page:   http://127.0.0.1:9641/
echo.
echo  Stopping any old console on 9641 / 11441 ...
powershell -NoProfile -Command "foreach ($p in 9641,11441,11442) { Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue } }"
timeout /t 2 /nobreak >nul
if defined LYGO_PYTHON if exist "%LYGO_PYTHON%" goto :run
if exist "C:\Python313\python.exe" set LYGO_PYTHON=C:\Python313\python.exe
if not defined LYGO_PYTHON set LYGO_PYTHON=py
:run
echo  Python: %LYGO_PYTHON%
echo.
"%LYGO_PYTHON%" -u "%CANON%\src\server.py" serve %*
if errorlevel 1 pause
