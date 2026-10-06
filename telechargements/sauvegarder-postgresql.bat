@echo off
setlocal
title NEXORA - Sauvegarde PostgreSQL
cd /d "%~dp0"

if not exist "%~dp0sauvegarder-postgresql.ps1" (
    echo [ERREUR] Le fichier sauvegarder-postgresql.ps1 manque.
    echo Placez les deux fichiers dans le dossier racine D:\NEXORA.
    pause
    exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0sauvegarder-postgresql.ps1"
set "NEXORA_EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %NEXORA_EXIT_CODE%
