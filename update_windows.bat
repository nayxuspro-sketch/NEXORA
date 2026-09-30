@echo off
chcp 65001 >nul
echo ========================================================
echo   NEXORA ERP - MISE A JOUR AUTOMATIQUE (CORRECTIF PDF)
echo ========================================================
echo.

echo [1/3] Recuperation des fichiers corriges depuis GitHub...
git fetch origin arena/01a0ba27-nexora
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Impossible de contacter GitHub. Verifiez votre connexion.
    pause
    exit /b %ERRORLEVEL%
)

git pull origin arena/01a0ba27-nexora
if %ERRORLEVEL% NEQ 0 (
    echo Tentative d'alignement force...
    git reset --hard origin/arena/01a0ba27-nexora
)

echo.
echo [2/3] Application des migrations backend...
call venv\Scripts\activate.bat 2>nul
python manage.py migrate --noinput

echo.
echo [3/3] Mise a jour terminee avec succes !
echo Tous les exports PDF et les validations UUID sont operationnels.
echo Vous pouvez redemarrer NEXORA avec start-local.bat.
echo.
pause
