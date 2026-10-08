@echo off
setlocal
cd /d "%~dp0"
title NEXORA ERP - POS

echo ================================================================
echo   NEXORA - demarrage local
echo ================================================================

if not exist ".venv\Scripts\python.exe" (
    echo Environnement Python absent. Suivez d'abord INSTALLATION-COMPLETE-NEXORA.md.
    goto :erreur
)
if not exist "frontend\node_modules\next" (
    echo Dependances frontend absentes. Dans frontend, executez : npm ci
    goto :erreur
)

if not exist "frontend\.env.local" (
    echo NEXT_PUBLIC_API_URL=http://127.0.0.1:8008/api/v1> "frontend\.env.local"
)

echo Demarrage du backend Django sur http://127.0.0.1:8008 ...
start "NEXORA Backend (Django 8008)" /D "%CD%" cmd /k ".venv\Scripts\python.exe manage.py runserver 127.0.0.1:8008"

echo Demarrage du frontend Next.js sur http://localhost:3000 ...
start "NEXORA Frontend (Next.js 3000)" /D "%CD%\frontend" cmd /k "npm run dev"

echo Le navigateur va s'ouvrir. Gardez les deux fenetres de serveur ouvertes.
timeout /t 5 /nobreak >nul
start "" "http://localhost:3000/"
exit /b 0

:erreur
echo.
pause
exit /b 1
