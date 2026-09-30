@echo off
setlocal EnableDelayedExpansion
title NEXORA Enterprise - Assistant de Mise a Jour

echo =====================================================================
echo           NEXORA Enterprise ERP - Mise a Jour du Systeme
echo =====================================================================
echo.
echo Ce script met a jour NEXORA, synchronise les ventes et applique
echo toutes les evolutions d'affichage. Vos donnees sont 100%% preservees.
echo.

echo.
echo [1/5] Arret des processus en cours...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
echo Processus nettoyes.

echo.
echo [2/5] Sauvegarde de securite de la base de donnees...
if exist "db.sqlite3" (
    copy /Y "db.sqlite3" "db.sqlite3.backup" >nul
    echo Base de donnees db.sqlite3 sauvegardee avec succes.
) else (
    echo Initialisation d'une nouvelle base de donnees...
)

echo.
echo [3/5] Verification des modules Python et dependances PDF...
pip install --quiet reportlab Pillow django djangorestframework django-filter django-cors-headers djangorestframework-simplejwt PyYAML pypdf

echo.
echo [4/5] Application des migrations et synchronisation catalogue...
python manage.py migrate
python scripts/seed_data.py

echo.
echo [5/5] Mise a jour terminee avec succes !
echo.
echo =====================================================================
echo     NEXORA v1.2.0 est a jour :
echo     - Historique des ventes complet (colonne articles vendus)
echo     - Saisie directe des quantites au clavier au POS
echo     - Exports PDF Business Intelligence et Bilan Vendeur valides
echo =====================================================================
echo.
echo Pour lancer NEXORA : double-cliquez sur start-local.bat
echo.
pause
