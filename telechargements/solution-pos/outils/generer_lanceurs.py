#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère les deux lanceurs autonomes du correctif POS.

  CORRIGER-POS-AUTONOME.bat   embarque corriger_bilan_vendeur_pos.py
  TESTER-BILAN-VENDEUR-POS.bat embarque fichiers/tests/test_bilan_vendeur_pos.py

Les scripts Python sont inclus en base64 : au lancement, le .bat les écrit dans
%TEMP%, les décode (certutil, puis PowerShell en secours) et les exécute.
Ainsi les .bat fonctionnent seuls, où qu'ils soient posés.

Usage :
    py outils/generer_lanceurs.py
"""
import base64
import os
import textwrap

DOSSIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------- CORRIGER-POS ----
ENTETE_CORRECTIF = r'''@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================================
echo  NEXORA - CORRECTIF POS AUTONOME v3
echo  Bilan de vente par vendeur : bouton "Mon Bilan Vente PDF" du POS
echo ============================================================================
echo.
echo Ce fichier est AUTONOME : le programme de correction est inclus dedans.
echo Aucun autre fichier n'est necessaire.
echo.

REM ---------------------------------------------------------------- dossiers --
set "RACINE=%~1"
if "%RACINE%"=="" if exist "C:\NEXORA\manage.py" set "RACINE=C:\NEXORA"
if "%RACINE%"=="" if exist "D:\NEXORA\manage.py" set "RACINE=D:\NEXORA"
if "%RACINE%"=="" for /d %%D in ("%USERPROFILE%\NEXORA*") do if exist "%%D\manage.py" set "RACINE=%%D"

set "RACINES="
if not "%~1"=="" set "RACINES=%~1"
if exist "D:\NEXORA\manage.py" set "RACINES=%RACINES%;D:\NEXORA"
if exist "C:\NEXORA\manage.py" set "RACINES=%RACINES%;C:\NEXORA"
if not "%RACINE%"=="" set "RACINES=%RACINES%;%RACINE%"
if "%RACINES%"=="" set "RACINES=%USERPROFILE%"
if "%RACINES:~0,1%"==";" set "RACINES=%RACINES:~1%"

echo Dossiers analyses : %RACINES%
echo.
echo Le script choisit lui-meme le bon projet : il retient le couple
echo vue PDF vendeur + ecran POS qui contient vraiment le bilan vendeur.
echo Il n'ecrit rien si un repere manque, et ne modifie rien si le correctif
echo est deja en place : relancer ce fichier est donc sans risque.
echo.

REM -------------------------------------------------- Python et script embarque --
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

set "TMPPOS=%TEMP%\nexora-correctif-pos"
if not exist "%TMPPOS%" mkdir "%TMPPOS%" >nul 2>nul
set "B64=%TMPPOS%\correctif.b64"
set "PYSCRIPT=%TMPPOS%\corriger_bilan_vendeur_pos.py"
del "%PYSCRIPT%" >nul 2>nul

> "%B64%" (
'''

PIED_CORRECTIF = r''')

certutil -f -decode "%B64%" "%PYSCRIPT%" >nul 2>nul
if not exist "%PYSCRIPT%" powershell -NoProfile -ExecutionPolicy Bypass -Command "$b=(Get-Content -Raw '%B64%') -replace '\s',''; [IO.File]::WriteAllBytes('%PYSCRIPT%',[Convert]::FromBase64String($b))" >nul 2>nul
if not exist "%PYSCRIPT%" (
  echo ERREUR : impossible d'extraire le programme de correction dans le dossier temporaire.
  echo Verifiez les droits d'acces a : %TMPPOS%
  echo.
  pause
  exit /b 4
)

REM ------------------------------------------------------------------ execution --
%PYEXE% "%PYSCRIPT%" --racines "%RACINES%"
set "CODE=%errorlevel%"

echo.
echo ============================================================================
if "%CODE%"=="0" (
  echo  ETAPE SUIVANTE : LANCER LE TEST
  echo ----------------------------------------------------------------------------
  echo  Double-cliquez sur  TESTER-BILAN-VENDEUR-POS.bat
  echo  Il ecrit le test dans le projet puis lance manage.py test.
  echo  Resultat attendu : OK, 14 tests.
  echo.
  echo  Si la sortie ci-dessus dit ARRET PARTIEL ou FICHIER INTROUVABLE, envoyez
  echo  plutot DIAGNOSTIC-POS.txt, cree a cote de ce .bat.
) else (
  echo  LE SCRIPT S'EST ARRETE AVANT DE TERMINER.
  echo  Aucun fichier pour lequel un repere manquait n'a ete ecrit, et les fichiers
  echo  deja corriges le restent. Envoyez DIAGNOSTIC-POS.txt, cree a cote de ce
  echo  .bat, avec la sortie affichee ci-dessus.
)
echo ============================================================================
echo.
pause
endlocal
'''

# --------------------------------------------------------------- TEST -----
ENTETE_TEST = r'''@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================================
echo  NEXORA - TEST du bilan de vente par vendeur au POS
echo ============================================================================
echo.
echo Ce fichier est AUTONOME : le test est inclus dedans. Il l'ecrit dans le
echo dossier "tests" du projet, puis lance manage.py test.
echo.

REM ------------------------------------------------------- dossier du projet --
set "PROJET=%~1"
if "%PROJET%"=="" if exist "C:\NEXORA\manage.py" set "PROJET=C:\NEXORA"
if "%PROJET%"=="" if exist "D:\NEXORA\manage.py" set "PROJET=D:\NEXORA"
if "%PROJET%"=="" for /d %%D in ("%USERPROFILE%\NEXORA*") do if exist "%%D\manage.py" set "PROJET=%%D"

if "%PROJET%"=="" (
  echo Projet introuvable : aucun manage.py dans C:\NEXORA, D:\NEXORA ou
  echo %USERPROFILE%\NEXORA* .
  echo Relancez en precisant le dossier, par exemple :
  echo    TESTER-BILAN-VENDEUR-POS.bat "C:\NEXORA"
  echo.
  pause
  exit /b 2
)
if not exist "%PROJET%\manage.py" (
  echo Ce dossier ne contient pas manage.py : %PROJET%
  echo.
  pause
  exit /b 2
)

echo Projet teste : %PROJET%
echo.

REM ------------------------------------------------------------------ Python --
set "PYEXE="
where py >nul 2>nul
if %errorlevel%==0 set "PYEXE=py -3"
if not defined PYEXE (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERREUR : Python introuvable sur ce PC.
    echo.
    pause
    exit /b 3
  )
  set "PYEXE=python"
)

REM ---------------------------------------------- ecriture du fichier de test --
if not exist "%PROJET%\tests" mkdir "%PROJET%\tests" >nul 2>nul
if not exist "%PROJET%\tests\__init__.py" type nul > "%PROJET%\tests\__init__.py"
if exist "%PROJET%\tests\test_bilan_vendeur_pos.py" copy /y "%PROJET%\tests\test_bilan_vendeur_pos.py" "%TEMP%\test_bilan_vendeur_pos.py.bak" >nul 2>nul

set "TMPPOS=%TEMP%\nexora-test-pos"
if not exist "%TMPPOS%" mkdir "%TMPPOS%" >nul 2>nul
set "B64=%TMPPOS%\test.b64"
set "FICHIER=%PROJET%\tests\test_bilan_vendeur_pos.py"
del "%FICHIER%" >nul 2>nul

> "%B64%" (
'''

PIED_TEST = r''')

certutil -f -decode "%B64%" "%FICHIER%" >nul 2>nul
if not exist "%FICHIER%" powershell -NoProfile -ExecutionPolicy Bypass -Command "$b=(Get-Content -Raw '%B64%') -replace '\s',''; [IO.File]::WriteAllBytes('%FICHIER%',[Convert]::FromBase64String($b))" >nul 2>nul
if not exist "%FICHIER%" (
  echo ERREUR : impossible d'ecrire le fichier de test dans %PROJET%\tests
  echo Verifiez les droits d'acces a ce dossier.
  echo.
  pause
  exit /b 4
)
echo Fichier de test ecrit : %FICHIER%
echo Une copie de sauvegarde de l'ancien fichier, s'il existait, est dans %TEMP%
echo.

REM -------------------------------------------------------------- execution --
pushd "%PROJET%"
%PYEXE% manage.py test tests.test_bilan_vendeur_pos -v 2
set "CODE=%errorlevel%"
popd

echo.
echo ============================================================================
if "%CODE%"=="0" (
  echo  RESULTAT : OK - les 14 tests passent.
  echo ----------------------------------------------------------------------------
  echo  Le bilan par vendeur fonctionne : filtrage strict par vendeur, ventes
  echo  annulees et brouillons exclus, vendeur inconnu refuse, caissier limite a
  echo  son propre bilan, export PDF genere.
  echo.
  echo  Il ne reste qu'a redemarrer le backend, puis le frontend dans son dossier :
  echo     npm run dev
  echo  et a utiliser le bouton Mon Bilan Vente PDF du POS.
) else (
  echo  RESULTAT : le test n'a pas abouti - code %CODE%
  echo ----------------------------------------------------------------------------
  echo  Lisez les lignes juste au-dessus. Cas les plus frequents :
  echo    - ImportError ou ModuleNotFoundError : un module manque dans
  echo      l'environnement Python, lancez pip install -r requirements.txt
  echo    - erreurs de base de donnees : PostgreSQL n'est pas demarre, ou le
  echo      fichier .env ne contient pas les bons acces.
  echo    - FAIL sur un test : envoyez ce texte, il indique exactement ce qui
  echo      cloche dans le bilan vendeur.
)
echo ============================================================================
echo.
pause
endlocal
'''


def construire(entete, pied, donnees, cible, taille_ligne=64):
    b64 = base64.b64encode(donnees).decode('ascii')
    lignes = textwrap.wrap(b64, taille_ligne)
    contenu = entete + ''.join('echo %s\r\n' % ligne for ligne in lignes) + pied

    problemes = [ligne for ligne in contenu.splitlines()
                 if ligne.strip().upper().startswith('ECHO')
                 and ('(' in ligne[5:] or ')' in ligne[5:])]
    if problemes:
        raise SystemExit('ERREUR : echo avec parenthèses ->\n' + '\n'.join(problemes))

    contenu = contenu.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
    with open(cible, 'w', encoding='utf-8', newline='') as fichier:
        fichier.write(contenu)
    return len(lignes), os.path.getsize(cible)


def verifier(cible, source):
    """Relit le .bat, extrait le base64 et le compare au fichier source."""
    contenu = open(cible, encoding='utf-8').read()
    lignes = contenu.split('\n')
    debut = next(i for i, l in enumerate(lignes) if l.strip().startswith('> "%B64%" ('))
    fin = next(i for i in range(debut + 1, len(lignes)) if lignes[i].strip() == ')')
    bloc = [l for l in lignes[debut + 1:fin] if l.strip()]
    b64 = ''.join(l[5:] for l in bloc)
    if base64.b64decode(b64) != open(source, 'rb').read():
        raise SystemExit('ERREUR : %s ne contient pas exactement %s' % (cible, source))
    brut = open(cible, 'rb').read()
    if brut.count(b'\r') != brut.count(b'\r\n'):
        raise SystemExit('ERREUR : fins de ligne non conformes dans %s' % cible)
    return len(bloc)


def main():
    script = os.path.join(DOSSIER, 'corriger_bilan_vendeur_pos.py')
    test = os.path.join(DOSSIER, 'fichiers', 'tests', 'test_bilan_vendeur_pos.py')

    cible1 = os.path.join(DOSSIER, 'CORRIGER-POS-AUTONOME.bat')
    n1, t1 = construire(ENTETE_CORRECTIF, PIED_CORRECTIF, open(script, 'rb').read(), cible1)
    print('%s : %d octets, %d lignes base64' % (os.path.basename(cible1), t1, n1))
    print('   vérification : %d lignes relues, contenu identique au script' % verifier(cible1, script))

    cible2 = os.path.join(DOSSIER, 'TESTER-BILAN-VENDEUR-POS.bat')
    n2, t2 = construire(ENTETE_TEST, PIED_TEST, open(test, 'rb').read(), cible2)
    print('%s : %d octets, %d lignes base64' % (os.path.basename(cible2), t2, n2))
    print('   vérification : %d lignes relues, contenu identique au test' % verifier(cible2, test))


if __name__ == '__main__':
    main()
