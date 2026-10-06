@echo off
setlocal
title NEXORA - PostgreSQL local
cd /d "%~dp0"

if not exist "%~dp0start-local-postgresql.ps1" (
    echo [ERREUR] Le fichier start-local-postgresql.ps1 manque.
    echo Placez les deux fichiers dans le dossier racine D:\NEXORA.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-local-postgresql.ps1"
set "NEXORA_EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %NEXORA_EXIT_CODE%
