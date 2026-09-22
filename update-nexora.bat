@echo off
setlocal EnableDelayedExpansion
title NEXORA Enterprise - Mise a jour du systeme

echo =====================================================================
echo           NEXORA Enterprise ERP - Assistant de Mise a Jour
echo =====================================================================
echo.
echo Ce script applique la mise a jour en preservant votre base de donnees.
echo.
pause

echo.
echo [1/4] Arret des processus en cours...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
echo Processus arretes.

echo.
echo [2/4] Sauvegarde de securite de la base de donnees...
if exist "db.sqlite3" (
    copy "db.sqlite3" "db.sqlite3.backup" >nul
    echo Base de donnees db.sqlite3 sauvegardee avec succes.
) else (
    echo Aucune base existante. Une nouvelle sera creee.
)

echo.
echo [3/4] Application des migrations de base de donnees...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Echec des migrations Django.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Mise a jour terminee avec succes !
echo.
echo =====================================================================
echo                NEXORA est pret a etre utilise !
echo =====================================================================
echo.
echo Vous pouvez maintenant lancer l'application avec : start-local.bat
echo Ou lancer le demarrage automatique avec : installer-demarrage-automatique.bat
echo.
pause
