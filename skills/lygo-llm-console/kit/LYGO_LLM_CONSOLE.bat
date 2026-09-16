@echo off
setlocal
set ROOT=%~dp0
cd /d "%ROOT%"
if defined LYGO_PYTHON if exist "%LYGO_PYTHON%" goto :run
if not defined LYGO_PYTHON if exist "C:\Python313\python.exe" set LYGO_PYTHON=C:\Python313\python.exe
if not defined LYGO_PYTHON set LYGO_PYTHON=py
:run
"%LYGO_PYTHON%" -u "%ROOT%src\server.py" serve %*
if errorlevel 1 pause
