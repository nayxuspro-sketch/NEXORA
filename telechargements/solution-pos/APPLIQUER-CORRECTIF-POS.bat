@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================================================
echo  NEXORA - Bilan de vente par vendeur au POS : correctif v2 (autodetection)
echo ============================================================================
echo.

REM 1. Detection des dossiers de projet : argument du .bat, puis D:\NEXORA, C:\NEXORA
set "RACINE=%~1"
set "RACINES="
if not "%RACINE%"=="" set "RACINES=%RACINE%"
if "%RACINE%"=="" if exist "D:\NEXORA" set "RACINES=%RACINES%;D:\NEXORA"
if "%RACINE%"=="" if exist "C:\NEXORA" set "RACINES=%RACINES%;C:\NEXORA"
if "%RACINE%"=="" for /d %%D in ("%USERPROFILE%\NEXORA*") do set "RACINES=%RACINES%;%%D"
if "%RACINES%"=="" set "RACINES=%USERPROFILE%"

REM nettoyage du premier point-virgule eventuel
if "%RACINES:~0,1%"==";" set "RACINES=%RACINES:~1%"

echo Dossiers analyses : %RACINES%
echo.
echo Le script cherche lui-meme les deux fichiers a corriger, meme si votre
echo projet n'a pas l'arborescence du depot.
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 corriger_bilan_vendeur_pos.py --racines "%RACINES%"
) else (
  python corriger_bilan_vendeur_pos.py --racines "%RACINES%"
)

echo.
echo ============================================================================
echo  A FAIRE MAINTENANT
echo ----------------------------------------------------------------------------
echo  1. Lisez ce qui est affiche juste au-dessus :
echo       - CORRECTIF EN PLACE.  -^> tout est bon, passez au point 2.
echo       - ARRET PARTIEL ou FICHIER INTROUVABLE -^> un fichier
echo         DIAGNOSTIC-POS.txt a ete cree A COTE DE CE .BAT.
echo         Envoyez ce fichier tel quel : il contient vos chemins et vos lignes.
echo.
echo  2. Test automatique : copiez d'abord le fichier
echo       fichiers\tests\test_bilan_vendeur_pos.py
echo     dans le dossier tests du projet, puis lancez :
echo       cd /d "%RACINE%"
echo       py manage.py test tests.test_bilan_vendeur_pos -v 2
echo.
echo  3. Redemarrez le backend puis le frontend, et utilisez le bouton
echo     Mon Bilan Vente PDF du POS.
echo ============================================================================
echo.
pause
endlocal
