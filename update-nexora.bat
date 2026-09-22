@echo off
chcp 65001 >nul
title NEXORA Enterprise - Assistant de Mise à Jour Automatique

echo =====================================================================
echo           NEXORA Enterprise ERP - Script de Mise à Jour
echo =====================================================================
echo.
echo Ce script applique la mise à jour tout en préservant intacte votre base
echo de données SQLite (ventes, stocks, utilisateurs, caisse).
echo.
pause

echo.
echo [1/4] Arrêt préventif des anciens processus en cours...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
echo Processus arrêtés avec succès.

echo.
echo [2/4] Sauvegarde de sécurité de votre base de données...
if exist db.sqlite3 (
    copy db.sqlite3 db.sqlite3.backup-%date:~6,4%%date:~3,2%%date:~0,2%-%time:~0,2%%time:~3,2% >nul
    echo Base de données db.sqlite3 sauvegardée avec succès.
) else (
    echo Aucune base existante à sauvegarder. Une nouvelle sera initialisée.
)

echo.
echo [3/4] Application des nouvelles migrations de base de données...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Échec de la mise à jour des tables. Vérifiez votre installation Python.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Finalisation des dépendances et de l'interface...
echo Mise à jour terminée avec succès !
echo.
echo =====================================================================
echo              Votre installation NEXORA est à jour !
echo =====================================================================
echo.
echo Pour démarrer NEXORA, double-cliquez sur : start-local.bat
echo Ou activez le démarrage automatique : installer-demarrage-automatique.bat
echo.
pause
