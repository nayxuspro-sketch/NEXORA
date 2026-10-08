@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================================================
echo  NEXORA - Bilan de vente par vendeur au POS : correctif automatique
echo ============================================================================
echo.

REM 1. Detection de la racine du projet : argument du .bat, puis D:\NEXORA, C:\NEXORA
set "RACINE=%~1"
if "%RACINE%"=="" if exist "D:\NEXORA\manage.py" set "RACINE=D:\NEXORA"
if "%RACINE%"=="" if exist "C:\NEXORA\manage.py" set "RACINE=C:\NEXORA"
if "%RACINE%"=="" for /d %%D in ("%USERPROFILE%\NEXORA*") do if exist "%%D\manage.py" set "RACINE=%%D"

if "%RACINE%"=="" (
  echo Projet introuvable automatiquement.
  echo Relancez en precisant le dossier, par exemple :
  echo    APPLIQUER-CORRECTIF-POS.bat "D:\NEXORA"
  echo.
  pause
  exit /b 2
)

echo Dossier du projet detecte : %RACINE%
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 corriger_bilan_vendeur_pos.py --racine "%RACINE%"
) else (
  python corriger_bilan_vendeur_pos.py --racine "%RACINE%"
)

echo.
echo ============================================================================
echo  ETAPE SUIVANTE : verifier avec le test automatique
echo ----------------------------------------------------------------------------
echo    cd /d "%RACINE%"
echo    py manage.py test tests.test_bilan_vendeur_pos -v 2
echo.
echo  Puis redemarrer le backend et le frontend, et utiliser le bouton
echo  "Mon Bilan Vente PDF" du POS : la liste deroulante remplace l'email.
echo ============================================================================
echo.
pause
endlocal
