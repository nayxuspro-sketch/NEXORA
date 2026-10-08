@echo off
setlocal
title NEXORA - Audit de securite pre-production
cd /d "%~dp0"

if not exist "%~dp0audit-securite-production.ps1" (
    echo [ERREUR] Le fichier audit-securite-production.ps1 manque.
    pause
    exit /b 1
)
if not exist "%~dp0audit_configuration_production.py" (
    echo [ERREUR] Le fichier audit_configuration_production.py manque.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0audit-securite-production.ps1"
set "NEXORA_EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %NEXORA_EXIT_CODE%
