@echo off
REM AI Arr Control - simple batch wrapper that forwards commands to the PowerShell helper
REM Usage: manage.bat <command> [options]

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage.ps1" %*

exit /b %ERRORLEVEL%
