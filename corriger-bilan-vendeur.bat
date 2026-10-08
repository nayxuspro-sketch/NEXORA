@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0corriger-bilan-vendeur.ps1"
set "NEXORA_EXIT_CODE=%ERRORLEVEL%"
echo.
pause
exit /b %NEXORA_EXIT_CODE%
