@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================================
echo  NEXORA - Bilan de vente par vendeur au POS : correctif v2
echo ============================================================================
echo.

REM --- 1. Dossiers de projet a analyser ---
set "RACINE=%~1"
if "%RACINE%"=="" if exist "D:\NEXORA\manage.py" set "RACINE=D:\NEXORA"
if "%RACINE%"=="" if exist "C:\NEXORA\manage.py" set "RACINE=C:\NEXORA"
if "%RACINE%"=="" for /d %%D in ("%USERPROFILE%\NEXORA*") do if exist "%%D\manage.py" set "RACINE=%%D"

set "RACINES="
if not "%~1"=="" set "RACINES=%~1"
if exist "D:\NEXORA" set "RACINES=%RACINES%;D:\NEXORA"
if exist "C:\NEXORA" set "RACINES=%RACINES%;C:\NEXORA"
for /d %%D in ("%USERPROFILE%\NEXORA*") do set "RACINES=%RACINES%;%%D"
if "%RACINES%"=="" set "RACINES=%USERPROFILE%"
if "%RACINES:~0,1%"==";" set "RACINES=%RACINES:~1%"

echo Dossiers analyses : %RACINES%
if not "%RACINE%"=="" echo Projet detecte    : %RACINE%
echo.

REM --- 2. Recherche du programme de correction ---
set "SCRIPT=%~dp0corriger_bilan_vendeur_pos.py"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0..\corriger_bilan_vendeur_pos.py"
if not exist "%SCRIPT%" if exist "D:\NEXORA\corriger_bilan_vendeur_pos.py" set "SCRIPT=D:\NEXORA\corriger_bilan_vendeur_pos.py"
if not exist "%SCRIPT%" if exist "C:\NEXORA\corriger_bilan_vendeur_pos.py" set "SCRIPT=C:\NEXORA\corriger_bilan_vendeur_pos.py"
if not exist "%SCRIPT%" for /d %%D in ("%USERPROFILE%\*") do if exist "%%D\corriger_bilan_vendeur_pos.py" set "SCRIPT=%%D\corriger_bilan_vendeur_pos.py"
if not exist "%SCRIPT%" for /d %%D in ("%USERPROFILE%\*\*") do if exist "%%D\corriger_bilan_vendeur_pos.py" set "SCRIPT=%%D\corriger_bilan_vendeur_pos.py"
if not exist "%SCRIPT%" for /d %%D in ("D:\*") do if exist "%%D\corriger_bilan_vendeur_pos.py" set "SCRIPT=%%D\corriger_bilan_vendeur_pos.py"
if not exist "%SCRIPT%" for /d %%D in ("C:\*") do if exist "%%D\corriger_bilan_vendeur_pos.py" set "SCRIPT=%%D\corriger_bilan_vendeur_pos.py"

if not exist "%SCRIPT%" (
  echo Programme de correction introuvable : corriger_bilan_vendeur_pos.py
  echo.
  echo Deux solutions, au choix :
  echo   A. Utilisez le fichier CORRIGER-POS-AUTONOME.bat : il est autonome, le
  echo      programme est inclus dedans, aucun autre fichier n'est necessaire.
  echo   B. Ou relancez ce .bat depuis le dossier extrait, qui contient a la fois
  echo      ce fichier et corriger_bilan_vendeur_pos.py.
  echo.
  pause
  exit /b 2
)

echo Programme de correction : %SCRIPT%
echo.

REM --- 3. Python ---
set "PYEXE="
where py >nul 2>nul
if %errorlevel%==0 set "PYEXE=py -3"
if not defined PYEXE (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERREUR : Python introuvable sur ce PC.
    echo Installez Python depuis https://www.python.org/downloads/ puis relancez.
    echo.
    pause
    exit /b 3
  )
  set "PYEXE=python"
)

REM --- 4. Execution ---
%PYEXE% "%SCRIPT%" --racines "%RACINES%"
set "CODE=%errorlevel%"

echo.
echo ============================================================================
if "%CODE%"=="0" (
  echo  A FAIRE MAINTENANT
  echo ----------------------------------------------------------------------------
  echo  1. Si la ligne ci-dessus dit CORRECTIF EN PLACE. c'est bon.
  echo     Sinon le fichier DIAGNOSTIC-POS.txt a ete cree a cote du programme de
  echo     correction : envoyez-le tel quel.
  echo.
  echo  2. Test automatique : copiez le fichier
  echo       fichiers\tests\test_bilan_vendeur_pos.py
  echo     dans le dossier "tests" de votre projet, puis lancez :
  echo       cd /d "%RACINE%"
  echo       py manage.py test tests.test_bilan_vendeur_pos -v 2
  echo.
  echo  3. Redemarrez le backend puis le frontend, et utilisez le bouton
  echo     Mon Bilan Vente PDF du POS.
) else (
  echo  LE SCRIPT S'EST ARRETE AVANT DE TERMINER - aucun fichier pour lequel un
  echo  repere manquait n'a ete ecrit. Envoyez DIAGNOSTIC-POS.txt, cree a cote du
  echo  programme, pour que la correction soit adaptee a vos lignes exactes.
)
echo ============================================================================
echo.
pause
endlocal
