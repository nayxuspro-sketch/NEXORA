@echo off
setlocal
title NEXORA - Verification du chemin Django
cd /d "%~dp0"

if not exist "%~dp0manage.py" (
    echo [ERREUR] manage.py est introuvable dans ce dossier.
    echo Extrayez les fichiers a cote de manage.py dans D:\NEXORA.
    pause
    exit /b 1
)
if not exist "%~dp0verifier_chemin_django.py" (
    echo [ERREUR] Le fichier verifier_chemin_django.py manque.
    pause
    exit /b 1
)

py "%~dp0verifier_chemin_django.py"
set "NEXORA_EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %NEXORA_EXIT_CODE%
