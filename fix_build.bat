@echo off
setlocal EnableDelayedExpansion
title NEXORA Enterprise - Synchronisation & Compilation

echo ==============================================================================
echo [NEXORA] Recompilation et Mise a Jour Totale de l'Application
echo ==============================================================================
echo.
echo 1. Arret des serveurs locaux...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo 2. Synchronisation de la base de donnees et des ventes...
python manage.py migrate
python scripts/seed_data.py

echo 3. Recompilation du Frontend Next.js (mise a jour des pages)...
cd frontend
call npm run build
cd ..

echo 4. Demarrage propre de NEXORA...
call start-local.bat
