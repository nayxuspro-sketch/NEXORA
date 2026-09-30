@echo off
setlocal EnableDelayedExpansion

title NEXORA - Configuration Demarrage Permanent

echo ==============================================================================
echo Activation du demarrage automatique permanent au demarrage de Windows...
echo ==============================================================================

set "TARGET_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo Creation du script de lancement automatique en arriere-plan...
copy /y "%~dp0scripts\nexora_autostart.vbs" "%TARGET_DIR%\NEXORA_Service.vbs" >nul

echo.
echo ==============================================================================
echo [SUCCES TOTAL] Configuration terminee avec succes !
echo.
echo A partir de maintenant :
echo 1. Des que vous allumez votre ordinateur, NEXORA tourne en arriere-plan.
echo 2. Aucune manipulation n'est necessaire, aucune fenetre noire ne s'affiche.
echo 3. Il vous suffit d'ouvrir Edge et de taper directement :
echo.
echo            http://localhost:3000/
echo.
echo ==============================================================================
pause
