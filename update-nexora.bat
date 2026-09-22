@echo off
setlocal EnableDelayedExpansion
title NEXORA Enterprise - Assistant de Mise a Jour

echo =====================================================================
echo           NEXORA Enterprise ERP - Mise a Jour du Systeme
echo =====================================================================
echo.
echo Ce script met a jour NEXORA, installe le moteur PDF ReportLab
echo et applique les migrations. Vos donnees sont 100% preservees.
echo.
pause

echo.
echo [1/5] Arret des processus existants...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
echo Anciens processus arretes.

echo.
echo [2/5] Sauvegarde de securite de votre base de donnees...
if exist "db.sqlite3" (
    copy "db.sqlite3" "db.sqlite3.backup" >nul
    echo Base de donnees db.sqlite3 sauvegardee avec succes.
) else (
    echo Aucune base existante. Une nouvelle sera creee.
)

echo.
echo [3/5] Installation et verification des modules PDF (reportlab, Pillow)...
pip install reportlab Pillow django djangorestframework django-filter django-cors-headers djangorestframework-simplejwt PyYAML
if %ERRORLEVEL% NEQ 0 (
    echo Tentative d'installation avec requirements...
    pip install -r requirements.txt
)

echo.
echo [4/5] Application des migrations de base de donnees...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Echec des migrations. Verifiez votre environnement Python.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [5/5] Mise a jour terminee avec succes !
echo.
echo =====================================================================
echo       NEXORA est a jour et tous les exports PDF sont prets !
echo =====================================================================
echo.
echo Pour lancer NEXORA : double-cliquez sur start-local.bat
echo.
pause
