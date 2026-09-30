@echo off
REM ==============================================================================
REM NEXORA ERP & POS - Lanceur avec fenetres ouvertes
REM ==============================================================================

cd /d "%~dp0"
title NEXORA Enterprise ERP

echo ==============================================================================
echo [NEXORA] Preparation & Demarrage des serveurs...
echo ==============================================================================

REM 1. Migration automatique de la base de donnees et initialisation
echo [1/3] Application des migrations de la base de donnees...
python manage.py migrate --noinput
if exist "seed_dev.py" (
    python seed_dev.py
)

REM 2. Fichier de configuration du port 8008
if not exist "frontend\.env.local" (
    echo NEXT_PUBLIC_API_URL=http://127.0.0.1:8008/api/v1> frontend\.env.local
)

REM 3. Lancement du Backend Django (fenetre visible)
echo [2/3] Lancement du Backend Django sur http://127.0.0.1:8008 ...
start "NEXORA Backend (Django 8008)" cmd /k "python manage.py runserver 127.0.0.1:8008"

REM 4. Lancement du Frontend Next.js (fenetre visible)
echo [3/3] Lancement du Frontend Next.js sur http://localhost:3000 ...
cd frontend
start "NEXORA Frontend (Next.js 3000)" cmd /k "npm run dev"
cd ..

REM 5. Attente et ouverture du navigateur sur localhost:3000
echo.
echo Ouverture de votre application dans 5 secondes...
timeout /t 5 /nobreak >nul
start http://localhost:3000/

echo.
echo Gardez les deux fenetres noires ouvertes pour que l'application reste active.
echo.
pause
