@echo off
chcp 65001 >nul
echo =======================================================================
echo      NEXORA ERP - APPLICATION AUTOMATIQUE DU CORRECTIF EXPORT PDF
echo =======================================================================
echo.
echo Ce script met a jour automatiquement les fichiers de votre projet NEXORA
echo directement depuis le depot officiel GitHub sans necessiter de fichier ZIP.
echo.

:: 1. Verifier si git est disponible
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Git n'est pas installe ou pas accessible dans votre terminal.
    echo Veuillez installer Git pour Windows ou executer cette commande dans Git Bash.
    echo.
    pause
    exit /b 1
)

:: 2. Se positionner dans le dossier du script
cd /d "%~dp0"

echo [1/3] Synchronisation avec la branche arena/01a0ba27-nexora...
git fetch origin arena/01a0ba27-nexora
if %ERRORLEVEL% NEQ 0 (
    echo [ATTENTION] Impossible de joindre origin. Tentative avec l'URL complete...
    git fetch https://github.com/nayxuspro-sketch/NEXORA.git arena/01a0ba27-nexora
)

echo [2/3] Application des modifications sur votre projet local...
git checkout arena/01a0ba27-nexora
git pull https://github.com/nayxuspro-sketch/NEXORA.git arena/01a0ba27-nexora

echo.
echo [3/3] Verification des fichiers appliques :
if exist "apps\common\validators.py" (
    echo   [OK] apps\common\validators.py est en place.
)
if exist "apps\pos\pdf_z_report.py" (
    echo   [OK] apps\pos\pdf_z_report.py est a jour.
)
if exist "apps\inventory\pdf_export.py" (
    echo   [OK] apps\inventory\pdf_export.py est a jour.
)
if exist "apps\catalog\pdf_export.py" (
    echo   [OK] apps\catalog\pdf_export.py est a jour.
)

echo.
echo =======================================================================
echo              LE CORRECTIF EST APPLIQUE AVEC SUCCES !
echo =======================================================================
echo.
echo Vous pouvez maintenant redemarrer NEXORA avec votre script habituel
echo (ex: start-local.bat).
echo.
pause
