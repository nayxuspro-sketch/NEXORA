@echo off
setlocal
title NEXORA - Inspection locale de settings.py
cd /d "%~dp0"

if not exist "%~dp0manage.py" (
    echo [ERREUR] manage.py est introuvable.
    echo Extrayez les fichiers a cote de manage.py dans D:\NEXORA.
    pause
    exit /b 1
)
if not exist "%~dp0inspecter_settings_securite.py" (
    echo [ERREUR] Le fichier inspecter_settings_securite.py manque.
    pause
    exit /b 1
)

py "%~dp0inspecter_settings_securite.py"
set "NEXORA_EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %NEXORA_EXIT_CODE%
