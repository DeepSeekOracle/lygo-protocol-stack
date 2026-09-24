@echo off
title LYGO image engine - fetch the checkpoint
powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File "%~dp0get_model.ps1" %*
