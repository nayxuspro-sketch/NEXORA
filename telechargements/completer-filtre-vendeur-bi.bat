@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0completer-filtre-vendeur-bi.ps1"
set "NEXORA_EXIT_CODE=%ERRORLEVEL%"
echo.
pause
exit /b %NEXORA_EXIT_CODE%
