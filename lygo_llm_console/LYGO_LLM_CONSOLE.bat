@echo off
setlocal
title LYGO LLM Console
set ROOT=%~dp0
cd /d "%ROOT%"
echo.
echo  LYGO LLM Console
echo  Portal  http://127.0.0.1:9641/
echo  Header: Scan drives  -  pick a model  -  Boot LLM
echo  Auto-scans %%USERPROFILE%%\.ollama\models and GGUF folders.
echo.
if defined LYGO_PYTHON if exist "%LYGO_PYTHON%" goto :run
if exist "U:\LYGO\projects\python\python.exe" set LYGO_PYTHON=U:\LYGO\projects\python\python.exe
if exist "F:\LYGO\projects\python\python.exe" set LYGO_PYTHON=F:\LYGO\projects\python\python.exe
if not defined LYGO_PYTHON if exist "C:\Python313\python.exe" set LYGO_PYTHON=C:\Python313\python.exe
if not defined LYGO_PYTHON set LYGO_PYTHON=py
:run
echo  Python: %LYGO_PYTHON%
echo.
"%LYGO_PYTHON%" -u "%ROOT%src\server.py" serve %*
if errorlevel 1 pause
