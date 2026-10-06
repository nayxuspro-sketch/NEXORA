@echo off
setlocal
title NEXORA - Profil de production dormant
cd /d "%~dp0"

if not exist "%~dp0manage.py" (
    echo [ERREUR] manage.py est introuvable.
    echo Extrayez les fichiers a cote de manage.py dans D:\NEXORA.
    pause
    exit /b 1
)
if not exist "%~dp0installer_profil_production.py" (
    echo [ERREUR] Le fichier installer_profil_production.py manque.
    pause
    exit /b 1
)

py "%~dp0installer_profil_production.py"
set "NEXORA_EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %NEXORA_EXIT_CODE%
