@echo off
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
echo IyAtKi0gY29kaW5nOiB1dGYtOCAtKi0KIiIiClRFU1QgZHUgwqsgQmlsYW4gZGUg
echo dmVudGUgcGFyIHZlbmRldXIgwrsgZHUgUE9TIOKAlCBmaWNoaWVyIEFVVE9OT01F
echo LgoKQXVjdW5lIGTDqXBlbmRhbmNlIMOgIHZvcyBhdXRyZXMgdGVzdHMgOiBjZSBm
echo aWNoaWVyIGNyw6llIGx1aS1tw6ptZSBzZXMgZG9ubsOpZXMKKGVudHJlcHJpc2Us
echo IHZlbmRldXJzLCBtYWdhc2luLCBwcm9kdWl0cywgdmVudGVzKSBwdWlzIGFwcGVs
echo bGUgbGUgdnJhaSBlbmRwb2ludAovYXBpL3YxL3NhbGVzL2V4cG9ydC1zZWxsZXIt
echo cGRmLyBldCB2w6lyaWZpZSBsZSBjb21wb3J0ZW1lbnQgcsOpZWwuCgpFeMOpY3V0
echo aW9uICjDoCBsYSByYWNpbmUgZHUgcHJvamV0LCBkb3NzaWVyIGRlIG1hbmFnZS5w
echo eSkgOgoKICAgIHB5IG1hbmFnZS5weSB0ZXN0IHRlc3RzLnRlc3RfYmlsYW5fdmVu
echo ZGV1cl9wb3MgLXYgMgoKUsOpc3VsdGF0IGF0dGVuZHUgOiBPSyAoMTQgdGVzdHMp
echo LgoKQ2UgcXVpIGVzdCB2w6lyaWZpw6kgOgogIDEuIGxlIGJpbGFuIG5lIGNvbnRp
echo ZW50IFFVRSBsZXMgdmVudGVzIGR1IHZlbmRldXIgY2hvaXNpIDsKICAyLiBsZXMg
echo YnJvdWlsbG9ucyBldCBsZXMgdmVudGVzIGFubnVsw6llcyBzb250IGV4Y2x1cyA7
echo CiAgMy4gdW4gdmVuZGV1ciBpbmNvbm51ID0+IDQwNCBleHBsaWNpdGUsIGphbWFp
echo cyBsZSBiaWxhbiBkJ3VuIGF1dHJlIDsKICA0LiB1biB2ZW5kZXVyIGQndW5lIEFV
echo VFJFIGVudHJlcHJpc2Ugbidlc3QgamFtYWlzIHV0aWxpc8OpIDsKICA1LiB1biBj
echo b21wdGUgQ0FTSElFUiBuJ29idGllbnQgcXVlIHNvbiBwcm9wcmUgYmlsYW4gOwog
echo IDYuIGwnZXhwb3J0IFBERiByw6lwb25kIGJpZW4gZXQgbm9tbWUgbGUgZmljaGll
echo ciBkJ2FwcsOocyBsZSB2ZW5kZXVyIGNob2lzaS4KIiIiCgppbXBvcnQganNvbgpm
echo cm9tIGRlY2ltYWwgaW1wb3J0IERlY2ltYWwKCmZyb20gZGphbmdvLnRlc3QgaW1w
echo b3J0IFRlc3RDYXNlCmZyb20gZGphbmdvLnV0aWxzIGltcG9ydCB0aW1lem9uZQpm
echo cm9tIHJlc3RfZnJhbWV3b3JrLnRlc3QgaW1wb3J0IEFQSUNsaWVudAoKZnJvbSBh
echo cHBzLmFjY291bnRzLm1vZGVscyBpbXBvcnQgVXNlciwgVXNlclJvbGUKZnJvbSBh
echo cHBzLmNhdGFsb2cubW9kZWxzIGltcG9ydCBDYXRlZ29yeSwgUHJvZHVjdCwgVW5p
echo dApmcm9tIGFwcHMuY29tcGFuaWVzLm1vZGVscyBpbXBvcnQgQ29tcGFueQpmcm9t
echo IGFwcHMuaW52ZW50b3J5Lm1vZGVscyBpbXBvcnQgU3RvcmUKZnJvbSBhcHBzLnNh
echo bGVzLm1vZGVscyBpbXBvcnQgU2FsZSwgU2FsZUl0ZW0sIFNhbGVTdGF0dXMKCiMg
echo TGVzIGhlbHBlcnMgZHUgY29ycmVjdGlmIHBvcnRlbnQgZGVzIG5vbXMgcHLDqWZp
echo eMOpcyAoX25leG9yYV8qKSBwb3VyIG5lIHBhcwojIGVudHJlciBlbiBjb25mbGl0
echo IGF2ZWMgdW4gYXV0cmUgY29ycmVjdGlmIDsgb24gYWNjZXB0ZSBhdXNzaSBsZXMg
echo YW5jaWVucyBub21zLgp0cnk6CiAgICBmcm9tIGFwcHMuc2FsZXMucGRmX3NlbGxl
echo cl9yZXBvcnQgaW1wb3J0ICgKICAgICAgICBfbmV4b3JhX3Jlc29sdmVfc2VsbGVy
echo IGFzIHJlc29sdmVfc2VsbGVyLAogICAgICAgIF9uZXhvcmFfdmVudGVzX2R1X3Zl
echo bmRldXIgYXMgc2FsZXNfcXVlcnlzZXRfZm9yX3NlbGxlciwKICAgICkKZXhjZXB0
echo IEltcG9ydEVycm9yOiAgIyBhbmNpZW5uZSB2ZXJzaW9uIGR1IGNvcnJlY3RpZgog
echo ICAgZnJvbSBhcHBzLnNhbGVzLnBkZl9zZWxsZXJfcmVwb3J0IGltcG9ydCByZXNv
echo bHZlX3NlbGxlciwgc2FsZXNfcXVlcnlzZXRfZm9yX3NlbGxlcgoKVVJMX0VYUE9S
echo VCA9ICcvYXBpL3YxL3NhbGVzL2V4cG9ydC1zZWxsZXItcGRmLycKCgpjbGFzcyBC
echo aWxhblZlbmRldXJQb3NUZXN0cyhUZXN0Q2FzZSk6CiAgICAiIiJCaWxhbiBkZSB2
echo ZW50ZSBwYXIgdmVuZGV1ciA6IGVuZHBvaW50IGV4cG9ydC1zZWxsZXItcGRmIGR1
echo IFBPUy4iIiIKCiAgICBAY2xhc3NtZXRob2QKICAgIGRlZiBzZXRVcFRlc3REYXRh
echo KGNscyk6CiAgICAgICAgY2xzLmNvbXBhbnkgPSBDb21wYW55Lm9iamVjdHMuY3Jl
echo YXRlKG5hbWU9J05leG9yYSBUZXN0Jywgc2x1Zz0nbmV4b3JhLXRlc3QnKQoKICAg
echo IGRlZiBzZXRVcChzZWxmKToKICAgICAgICBzZWxmLmNvbXBhbnkgPSBzZWxmLl9f
echo Y2xhc3NfXy5jb21wYW55CgogICAgICAgIHNlbGYuYWRtaW5pc3RyYXRldXIgPSBV
echo c2VyLm9iamVjdHMuY3JlYXRlX3VzZXIoCiAgICAgICAgICAgIGVtYWlsPSdhZG1p
echo bi50ZXN0QG5leG9yYS5sb2NhbCcsIHBhc3N3b3JkPSdQYXNzd29yZDEyMyEnLAog
echo ICAgICAgICAgICBmaXJzdF9uYW1lPSdBZG1pbicsIGxhc3RfbmFtZT0nVGVzdCcs
echo CiAgICAgICAgICAgIGNvbXBhbnk9c2VsZi5jb21wYW55LCByb2xlPVVzZXJSb2xl
echo LkFETUlOKQogICAgICAgIHNlbGYudmVuZGV1cjEgPSBVc2VyLm9iamVjdHMuY3Jl
echo YXRlX3VzZXIoCiAgICAgICAgICAgIGVtYWlsPSdhd2EudHJhb3JlQG5leG9yYS5s
echo b2NhbCcsIHBhc3N3b3JkPSdQYXNzd29yZDEyMyEnLAogICAgICAgICAgICBmaXJz
echo dF9uYW1lPSdBd2EnLCBsYXN0X25hbWU9J1RyYW9yZScsCiAgICAgICAgICAgIGNv
echo bXBhbnk9c2VsZi5jb21wYW55LCByb2xlPVVzZXJSb2xlLkNBU0hJRVIpCiAgICAg
echo ICAgc2VsZi52ZW5kZXVyMiA9IFVzZXIub2JqZWN0cy5jcmVhdGVfdXNlcigKICAg
echo ICAgICAgICAgZW1haWw9J2JvdWJhY2FyLmtvbmVAbmV4b3JhLmxvY2FsJywgcGFz
echo c3dvcmQ9J1Bhc3N3b3JkMTIzIScsCiAgICAgICAgICAgIGZpcnN0X25hbWU9J0Jv
echo dWJhY2FyJywgbGFzdF9uYW1lPSdLb25lJywKICAgICAgICAgICAgY29tcGFueT1z
echo ZWxmLmNvbXBhbnksIHJvbGU9VXNlclJvbGUuQ0FTSElFUikKCiAgICAgICAgc2Vs
echo Zi5hdXRyZV9lbnRyZXByaXNlID0gQ29tcGFueS5vYmplY3RzLmNyZWF0ZShuYW1l
echo PSdCZXRhIFRlc3QnLCBzbHVnPSdiZXRhLXRlc3QnKQogICAgICAgIHNlbGYudXRp
echo bGlzYXRldXJfYmV0YSA9IFVzZXIub2JqZWN0cy5jcmVhdGVfdXNlcigKICAgICAg
echo ICAgICAgZW1haWw9J2NoZWZAYmV0YS5sb2NhbCcsIHBhc3N3b3JkPSdQYXNzd29y
echo ZDEyMyEnLAogICAgICAgICAgICBmaXJzdF9uYW1lPSdDaGVmJywgbGFzdF9uYW1l
echo PSdCZXRhJywKICAgICAgICAgICAgY29tcGFueT1zZWxmLmF1dHJlX2VudHJlcHJp
echo c2UsIHJvbGU9VXNlclJvbGUuQURNSU4pCgogICAgICAgIHNlbGYubWFnYXNpbiA9
echo IFN0b3JlLm9iamVjdHMuY3JlYXRlKGNvbXBhbnk9c2VsZi5jb21wYW55LCBuYW1l
echo PSdNYWdhc2luIFRlc3QnLCBjb2RlPSdNQUctVCcpCiAgICAgICAgc2VsZi5tYWdh
echo c2luX2JldGEgPSBTdG9yZS5vYmplY3RzLmNyZWF0ZSgKICAgICAgICAgICAgY29t
echo cGFueT1zZWxmLmF1dHJlX2VudHJlcHJpc2UsIG5hbWU9J01hZ2FzaW4gQmV0YScs
echo IGNvZGU9J01BRy1CJykKCiAgICAgICAgc2VsZi5jYXRlZ29yaWUgPSBDYXRlZ29y
echo eS5vYmplY3RzLmNyZWF0ZShjb21wYW55PXNlbGYuY29tcGFueSwgbmFtZT0nRGl2
echo ZXJzJywgc2x1Zz0nZGl2ZXJzJykKICAgICAgICBzZWxmLnVuaXRlID0gVW5pdC5v
echo YmplY3RzLmNyZWF0ZShjb21wYW55PXNlbGYuY29tcGFueSwgbmFtZT0nUGllY2Un
echo LCBzeW1ib2w9J3BjcycpCiAgICAgICAgc2VsZi5wcm9kdWl0ID0gUHJvZHVjdC5v
echo YmplY3RzLmNyZWF0ZSgKICAgICAgICAgICAgY29tcGFueT1zZWxmLmNvbXBhbnks
echo IG5hbWU9J0FydGljbGUgVGVzdCcsIHNrdT0nQVJULVRFU1QtMDEnLAogICAgICAg
echo ICAgICBjYXRlZ29yeT1zZWxmLmNhdGVnb3JpZSwgdW5pdD1zZWxmLnVuaXRlLAog
echo ICAgICAgICAgICBjb3N0X3ByaWNlPURlY2ltYWwoJzEwMC4wMCcpLCBzZWxsaW5n
echo X3ByaWNlPURlY2ltYWwoJzEwMDAuMDAnKSkKICAgICAgICBzZWxmLnByb2R1aXRf
echo YmV0YSA9IFByb2R1Y3Qub2JqZWN0cy5jcmVhdGUoCiAgICAgICAgICAgIGNvbXBh
echo bnk9c2VsZi5hdXRyZV9lbnRyZXByaXNlLCBuYW1lPSdBcnRpY2xlIEJldGEnLCBz
echo a3U9J0FSVC1CRVRBLTAxJywKICAgICAgICAgICAgY29zdF9wcmljZT1EZWNpbWFs
echo KCcxMDAuMDAnKSwgc2VsbGluZ19wcmljZT1EZWNpbWFsKCcxMDAwLjAwJykpCgog
echo ICAgICAgIHNlbGYuY2xpZW50X2FkbWluID0gQVBJQ2xpZW50KCkKICAgICAgICBz
echo ZWxmLmNsaWVudF9hZG1pbi5mb3JjZV9hdXRoZW50aWNhdGUodXNlcj1zZWxmLmFk
echo bWluaXN0cmF0ZXVyKQogICAgICAgIHNlbGYuY2xpZW50X3ZlbmRldXIxID0gQVBJ
echo Q2xpZW50KCkKICAgICAgICBzZWxmLmNsaWVudF92ZW5kZXVyMS5mb3JjZV9hdXRo
echo ZW50aWNhdGUodXNlcj1zZWxmLnZlbmRldXIxKQoKICAgICAgICBhdWpvdXJkaHVp
echo ID0gdGltZXpvbmUubG9jYWxkYXRlKCkKCiAgICAgICAgIyBWZW50ZXMgZHUgdmVu
echo ZGV1ciAxIDogMSAwMDAgKyAyIDAwMCA9IDMgMDAwCiAgICAgICAgc2VsZi52ZW50
echo ZTEgPSBzZWxmLl9jcmVlcl92ZW50ZSgnVEVTVC1WMS0wMDEnLCBzZWxmLnZlbmRl
echo dXIxLCBEZWNpbWFsKCcxMDAwLjAwJykpCiAgICAgICAgc2VsZi52ZW50ZTIgPSBz
echo ZWxmLl9jcmVlcl92ZW50ZSgnVEVTVC1WMS0wMDInLCBzZWxmLnZlbmRldXIxLCBE
echo ZWNpbWFsKCcyMDAwLjAwJykpCiAgICAgICAgIyBWZW50ZSBkdSB2ZW5kZXVyIDIg
echo OiA0IDAwMAogICAgICAgIHNlbGYudmVudGUzID0gc2VsZi5fY3JlZXJfdmVudGUo
echo J1RFU1QtVjItMDAxJywgc2VsZi52ZW5kZXVyMiwgRGVjaW1hbCgnNDAwMC4wMCcp
echo KQoKICAgICAgICAjIENhcyBleGNsdXMgZHUgYmlsYW4KICAgICAgICBzZWxmLnZl
echo bnRlX2FubnVsZWUgPSBzZWxmLl9jcmVlcl92ZW50ZSgKICAgICAgICAgICAgJ1RF
echo U1QtVjEtQU5OVUxFRScsIHNlbGYudmVuZGV1cjEsIERlY2ltYWwoJzk5OTkuMDAn
echo KSwgc3RhdHV0PVNhbGVTdGF0dXMuQ0FOQ0VMTEVEKQogICAgICAgIHNlbGYudmVu
echo dGVfYnJvdWlsbG9uID0gc2VsZi5fY3JlZXJfdmVudGUoCiAgICAgICAgICAgICdU
echo RVNULVYxLUJST1VJTExPTicsIHNlbGYudmVuZGV1cjEsIERlY2ltYWwoJzg4ODgu
echo MDAnKSwgc3RhdHV0PVNhbGVTdGF0dXMuRFJBRlQpCiAgICAgICAgc2VsZi52ZW50
echo ZV9zYW5zX3ZlbmRldXIgPSBzZWxmLl9jcmVlcl92ZW50ZSgnVEVTVC1TQU5TLVZF
echo TkRFVVInLCBOb25lLCBEZWNpbWFsKCc3Nzc3LjAwJykpCiAgICAgICAgc2VsZi52
echo ZW50ZV9ob3JzX3BlcmlvZGUgPSBzZWxmLl9jcmVlcl92ZW50ZSgKICAgICAgICAg
echo ICAgJ1RFU1QtVjEtVklFSUxMRScsIHNlbGYudmVuZGV1cjEsIERlY2ltYWwoJzY2
echo NjYuMDAnKSwgam91cnNfZW5fYXJyaWVyZT05MCkKICAgICAgICBzZWxmLnZlbnRl
echo X2F1dHJlX2VudHJlcHJpc2UgPSBzZWxmLl9jcmVlcl92ZW50ZSgKICAgICAgICAg
echo ICAgJ1RFU1QtQkVUQS0wMDEnLCBzZWxmLnV0aWxpc2F0ZXVyX2JldGEsIERlY2lt
echo YWwoJzU1NTUuMDAnKSwKICAgICAgICAgICAgZW50cmVwcmlzZT1zZWxmLmF1dHJl
echo X2VudHJlcHJpc2UsIG1hZ2FzaW49c2VsZi5tYWdhc2luX2JldGEsCiAgICAgICAg
echo ICAgIHByb2R1aXQ9c2VsZi5wcm9kdWl0X2JldGEpCgogICAgICAgIHNlbGYuZGVi
echo dXQgPSAoYXVqb3VyZGh1aSAtIHRpbWV6b25lLnRpbWVkZWx0YShkYXlzPTMwKSku
echo aXNvZm9ybWF0KCkKICAgICAgICBzZWxmLmZpbiA9IGF1am91cmRodWkuaXNvZm9y
echo bWF0KCkKICAgICAgICBzZWxmLmZlbmV0cmVfZGVidXQgPSB0aW1lem9uZS5ub3co
echo KSAtIHRpbWV6b25lLnRpbWVkZWx0YShkYXlzPTMwKQogICAgICAgIHNlbGYuZmVu
echo ZXRyZV9maW4gPSB0aW1lem9uZS5ub3coKSArIHRpbWV6b25lLnRpbWVkZWx0YSho
echo b3Vycz00KQoKICAgICMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBvdXRpbHMgLS0KCiAgICBkZWYg
echo X2NyZWVyX3ZlbnRlKHNlbGYsIHJlZmVyZW5jZSwgdmVuZGV1ciwgbW9udGFudCwg
echo c3RhdHV0PVNhbGVTdGF0dXMuQ09NUExFVEVELAogICAgICAgICAgICAgICAgICAg
echo ICAgam91cnNfZW5fYXJyaWVyZT0wLCBlbnRyZXByaXNlPU5vbmUsIG1hZ2FzaW49
echo Tm9uZSwgcHJvZHVpdD1Ob25lKToKICAgICAgICBlbnRyZXByaXNlID0gZW50cmVw
echo cmlzZSBvciBzZWxmLmNvbXBhbnkKICAgICAgICBtYWdhc2luID0gbWFnYXNpbiBv
echo ciBzZWxmLm1hZ2FzaW4KICAgICAgICBwcm9kdWl0ID0gcHJvZHVpdCBvciBzZWxm
echo LnByb2R1aXQKICAgICAgICB2ZW50ZSA9IFNhbGUub2JqZWN0cy5jcmVhdGUoCiAg
echo ICAgICAgICAgIGNvbXBhbnk9ZW50cmVwcmlzZSwgcmVmZXJlbmNlPXJlZmVyZW5j
echo ZSwgc3RvcmU9bWFnYXNpbiwgc2VsbGVyPXZlbmRldXIsCiAgICAgICAgICAgIHN0
echo YXR1cz1zdGF0dXQsIHN1YnRvdGFsX2Ftb3VudD1tb250YW50LCB0b3RhbF9hbW91
echo bnQ9bW9udGFudCwKICAgICAgICAgICAgcGFpZF9hbW91bnQ9bW9udGFudCBpZiBz
echo dGF0dXQgPT0gU2FsZVN0YXR1cy5DT01QTEVURUQgZWxzZSBEZWNpbWFsKCcwLjAw
echo JykpCiAgICAgICAgU2FsZUl0ZW0ub2JqZWN0cy5jcmVhdGUoCiAgICAgICAgICAg
echo IGNvbXBhbnk9ZW50cmVwcmlzZSwgc2FsZT12ZW50ZSwgcHJvZHVjdD1wcm9kdWl0
echo LAogICAgICAgICAgICBxdWFudGl0eT1EZWNpbWFsKCcxLjAwJyksIHVuaXRfcHJp
echo Y2U9bW9udGFudCwKICAgICAgICAgICAgdGF4X3JhdGU9RGVjaW1hbCgnMC4wMCcp
echo LCB0b3RhbD1tb250YW50KQogICAgICAgIGlmIGpvdXJzX2VuX2FycmllcmU6CiAg
echo ICAgICAgICAgIGRhdGUgPSB0aW1lem9uZS5ub3coKSAtIHRpbWV6b25lLnRpbWVk
echo ZWx0YShkYXlzPWpvdXJzX2VuX2FycmllcmUpCiAgICAgICAgICAgIFNhbGUub2Jq
echo ZWN0cy5maWx0ZXIocGs9dmVudGUucGspLnVwZGF0ZShjcmVhdGVkX2F0PWRhdGUp
echo CiAgICAgICAgICAgIHZlbnRlLnJlZnJlc2hfZnJvbV9kYigpCiAgICAgICAgcmV0
echo dXJuIHZlbnRlCgogICAgZGVmIF9ub21fZmljaGllcihzZWxmLCByZXBvbnNlKToK
echo ICAgICAgICByZXR1cm4gcmVwb25zZS5nZXQoJ0NvbnRlbnQtRGlzcG9zaXRpb24n
echo LCAnJykKCiAgICAjIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
echo LS0tLS0tLS0tLS0tLS0gMS4gZmlsdHJlIHZlbmRldXIgLS0KCiAgICBkZWYgdGVz
echo dF9xdWVyeXNldF9saW1pdGVfYXVfdmVuZGV1cl9ldF9hX2xhX3BlcmlvZGUoc2Vs
echo Zik6CiAgICAgICAgcXMgPSBzYWxlc19xdWVyeXNldF9mb3Jfc2VsbGVyKAogICAg
echo ICAgICAgICBzZWxmLmNvbXBhbnksIHNlbGYudmVuZGV1cjEsIHNlbGYuZmVuZXRy
echo ZV9kZWJ1dCwgc2VsZi5mZW5ldHJlX2ZpbikKICAgICAgICByZWZlcmVuY2VzID0g
echo c29ydGVkKHFzLnZhbHVlc19saXN0KCdyZWZlcmVuY2UnLCBmbGF0PVRydWUpKQog
echo ICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwocmVmZXJlbmNlcywgWydURVNULVYxLTAw
echo MScsICdURVNULVYxLTAwMiddKQogICAgICAgIHRvdGFsID0gc3VtKCh2LnRvdGFs
echo X2Ftb3VudCBmb3IgdiBpbiBxcyksIERlY2ltYWwoJzAuMDAnKSkKICAgICAgICBz
echo ZWxmLmFzc2VydEVxdWFsKHRvdGFsLCBEZWNpbWFsKCczMDAwLjAwJykpCgogICAg
echo ZGVmIHRlc3RfdmVudGVzX2FubnVsZWVzX2Jyb3VpbGxvbnNfZXRfaG9yc19wZXJp
echo b2RlX2V4Y2x1cyhzZWxmKToKICAgICAgICBxcyA9IHNhbGVzX3F1ZXJ5c2V0X2Zv
echo cl9zZWxsZXIoCiAgICAgICAgICAgIHNlbGYuY29tcGFueSwgc2VsZi52ZW5kZXVy
echo MSwgc2VsZi5mZW5ldHJlX2RlYnV0LCBzZWxmLmZlbmV0cmVfZmluKQogICAgICAg
echo IHJlZmVyZW5jZXMgPSBzZXQocXMudmFsdWVzX2xpc3QoJ3JlZmVyZW5jZScsIGZs
echo YXQ9VHJ1ZSkpCiAgICAgICAgZm9yIGV4Y2x1ZSBpbiAoJ1RFU1QtVjEtQU5OVUxF
echo RScsICdURVNULVYxLUJST1VJTExPTicsICdURVNULVYxLVZJRUlMTEUnLAogICAg
echo ICAgICAgICAgICAgICAgICAgICdURVNULVNBTlMtVkVOREVVUicpOgogICAgICAg
echo ICAgICBzZWxmLmFzc2VydE5vdEluKGV4Y2x1ZSwgcmVmZXJlbmNlcykKCiAgICBk
echo ZWYgdGVzdF9sZV92ZW5kZXVyMl9uZV92b2l0X3F1ZV9zZXNfdmVudGVzKHNlbGYp
echo OgogICAgICAgIHFzID0gc2FsZXNfcXVlcnlzZXRfZm9yX3NlbGxlcigKICAgICAg
echo ICAgICAgc2VsZi5jb21wYW55LCBzZWxmLnZlbmRldXIyLCBzZWxmLmZlbmV0cmVf
echo ZGVidXQsIHNlbGYuZmVuZXRyZV9maW4pCiAgICAgICAgc2VsZi5hc3NlcnRFcXVh
echo bChzb3J0ZWQocXMudmFsdWVzX2xpc3QoJ3JlZmVyZW5jZScsIGZsYXQ9VHJ1ZSkp
echo LCBbJ1RFU1QtVjItMDAxJ10pCgogICAgZGVmIHRlc3RfY2xvaXNvbm5lbWVudF9l
echo bnRyZV9lbnRyZXByaXNlcyhzZWxmKToKICAgICAgICBxcyA9IHNhbGVzX3F1ZXJ5
echo c2V0X2Zvcl9zZWxsZXIoCiAgICAgICAgICAgIHNlbGYuY29tcGFueSwgc2VsZi52
echo ZW5kZXVyMiwgc2VsZi5mZW5ldHJlX2RlYnV0LCBzZWxmLmZlbmV0cmVfZmluKQog
echo ICAgICAgIHNlbGYuYXNzZXJ0Tm90SW4oJ1RFU1QtQkVUQS0wMDEnLCBzZXQocXMu
echo dmFsdWVzX2xpc3QoJ3JlZmVyZW5jZScsIGZsYXQ9VHJ1ZSkpKQoKICAgICMgLS0t
echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIDIu
echo IHJlc29sdmVfc2VsbGVyIC0tCgogICAgZGVmIHRlc3RfcmVzb2x2ZV9zZWxsZXJf
echo aWRlbnRpZmllX2xlX2Jvbl9jb21wdGUoc2VsZik6CiAgICAgICAgZm9yIGNpYmxl
echo IGluIChzdHIoc2VsZi52ZW5kZXVyMS5pZCksICdhd2EudHJhb3JlQG5leG9yYS5s
echo b2NhbCcsCiAgICAgICAgICAgICAgICAgICAgICAnQVdBLlRSQU9SRUBORVhPUkEu
echo TE9DQUwnLCAnYXdhLnRyYW9yZScsICdBd2EgVHJhb3JlJyk6CiAgICAgICAgICAg
echo IHZlbmRldXIsIGVycmV1ciA9IHJlc29sdmVfc2VsbGVyKHNlbGYuY29tcGFueSwg
echo Y2libGUpCiAgICAgICAgICAgIHNlbGYuYXNzZXJ0SXNOb25lKGVycmV1ciwgJ0Np
echo YmxlICVzIDogYXVjdW5lIGVycmV1ciBhdHRlbmR1ZScgJSBjaWJsZSkKICAgICAg
echo ICAgICAgc2VsZi5hc3NlcnRFcXVhbCh2ZW5kZXVyLCBzZWxmLnZlbmRldXIxLCAn
echo Q2libGUgJXMnICUgY2libGUpCgogICAgZGVmIHRlc3RfcmVzb2x2ZV9zZWxsZXJf
echo cmVmdXNlX3VuX3ZlbmRldXJfaW5jb25udShzZWxmKToKICAgICAgICB2ZW5kZXVy
echo LCBlcnJldXIgPSByZXNvbHZlX3NlbGxlcihzZWxmLmNvbXBhbnksICdwZXJzb25u
echo ZS5pbmNvbm51ZUBuZXhvcmEubG9jYWwnKQogICAgICAgIHNlbGYuYXNzZXJ0SXNO
echo b25lKHZlbmRldXIpCiAgICAgICAgc2VsZi5hc3NlcnRJc05vdE5vbmUoZXJyZXVy
echo KQoKICAgIGRlZiB0ZXN0X3Jlc29sdmVfc2VsbGVyX3JlZnVzZV91bl9lbWFpbF9w
echo YXJ0aWVsX2FtYmlndShzZWxmKToKICAgICAgICBVc2VyLm9iamVjdHMuY3JlYXRl
echo X3VzZXIoCiAgICAgICAgICAgIGVtYWlsPSdhd2EudHJhb3JlMkBuZXhvcmEubG9j
echo YWwnLCBwYXNzd29yZD0nUGFzc3dvcmQxMjMhJywKICAgICAgICAgICAgZmlyc3Rf
echo bmFtZT0nQXdhJywgbGFzdF9uYW1lPSdUcmFvcmUgQmlzJywKICAgICAgICAgICAg
echo Y29tcGFueT1zZWxmLmNvbXBhbnksIHJvbGU9VXNlclJvbGUuQ0FTSElFUikKICAg
echo ICAgICB2ZW5kZXVyLCBlcnJldXIgPSByZXNvbHZlX3NlbGxlcihzZWxmLmNvbXBh
echo bnksICdhd2EudHJhb3JlJykKICAgICAgICBzZWxmLmFzc2VydElzTm9uZSh2ZW5k
echo ZXVyKQogICAgICAgIHNlbGYuYXNzZXJ0SXNOb3ROb25lKGVycmV1cikKCiAgICBk
echo ZWYgdGVzdF9yZXNvbHZlX3NlbGxlcl9yZWZ1c2VfdW5fdmVuZGV1cl9kX3VuZV9h
echo dXRyZV9lbnRyZXByaXNlKHNlbGYpOgogICAgICAgIGZvciBjaWJsZSBpbiAoc3Ry
echo KHNlbGYudXRpbGlzYXRldXJfYmV0YS5pZCksICdjaGVmQGJldGEubG9jYWwnKToK
echo ICAgICAgICAgICAgdmVuZGV1ciwgZXJyZXVyID0gcmVzb2x2ZV9zZWxsZXIoc2Vs
echo Zi5jb21wYW55LCBjaWJsZSkKICAgICAgICAgICAgc2VsZi5hc3NlcnRJc05vbmUo
echo dmVuZGV1ciwgJ0NpYmxlICVzJyAlIGNpYmxlKQogICAgICAgICAgICBzZWxmLmFz
echo c2VydElzTm90Tm9uZShlcnJldXIsICdDaWJsZSAlcycgJSBjaWJsZSkKCiAgICAj
echo IC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
echo LS0gMy4gZXhwb3J0IFBERiAtLS0tCgogICAgZGVmIHRlc3RfZXhwb3J0X3BkZl9k
echo dV92ZW5kZXVyX2Nob2lzaShzZWxmKToKICAgICAgICByZXBvbnNlID0gc2VsZi5j
echo bGllbnRfdmVuZGV1cjEuZ2V0KAogICAgICAgICAgICBVUkxfRVhQT1JULCB7J3N0
echo YXJ0X2RhdGUnOiBzZWxmLmRlYnV0LCAnZW5kX2RhdGUnOiBzZWxmLmZpbiwKICAg
echo ICAgICAgICAgICAgICAgICAgICAgICdzZWxsZXJfaWQnOiBzdHIoc2VsZi52ZW5k
echo ZXVyMS5pZCl9KQogICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwocmVwb25zZS5zdGF0
echo dXNfY29kZSwgMjAwKQogICAgICAgIHNlbGYuYXNzZXJ0SW4oJ2FwcGxpY2F0aW9u
echo L3BkZicsIHJlcG9uc2VbJ0NvbnRlbnQtVHlwZSddKQogICAgICAgIG5vbSA9IHNl
echo bGYuX25vbV9maWNoaWVyKHJlcG9uc2UpCiAgICAgICAgc2VsZi5hc3NlcnRJbign
echo QXdhX1RyYW9yZScsIG5vbSkKICAgICAgICBzZWxmLmFzc2VydE5vdEluKCdCb3Vi
echo YWNhcicsIG5vbSkKCiAgICBkZWYgdGVzdF9leHBvcnRfcGRmX3ZlbmRldXIyX25l
echo X2NvbnRpZW50X3Bhc19sZV92ZW5kZXVyMShzZWxmKToKICAgICAgICByZXBvbnNl
echo ID0gc2VsZi5jbGllbnRfYWRtaW4uZ2V0KAogICAgICAgICAgICBVUkxfRVhQT1JU
echo LCB7J3N0YXJ0X2RhdGUnOiBzZWxmLmRlYnV0LCAnZW5kX2RhdGUnOiBzZWxmLmZp
echo biwKICAgICAgICAgICAgICAgICAgICAgICAgICdzZWxsZXJfaWQnOiBzdHIoc2Vs
echo Zi52ZW5kZXVyMi5pZCl9KQogICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwocmVwb25z
echo ZS5zdGF0dXNfY29kZSwgMjAwKQogICAgICAgIG5vbSA9IHNlbGYuX25vbV9maWNo
echo aWVyKHJlcG9uc2UpCiAgICAgICAgc2VsZi5hc3NlcnRJbignQm91YmFjYXJfS29u
echo ZScsIG5vbSkKICAgICAgICBzZWxmLmFzc2VydE5vdEluKCdBd2EnLCBub20pCgog
echo ICAgZGVmIHRlc3RfZXhwb3J0X3BkZl92ZW5kZXVyX2luY29ubnVfcmVudm9pZV80
echo MDQoc2VsZik6CiAgICAgICAgcmVwb25zZSA9IHNlbGYuY2xpZW50X2FkbWluLmdl
echo dCgKICAgICAgICAgICAgVVJMX0VYUE9SVCwgeydzdGFydF9kYXRlJzogc2VsZi5k
echo ZWJ1dCwgJ2VuZF9kYXRlJzogc2VsZi5maW4sCiAgICAgICAgICAgICAgICAgICAg
echo ICAgICAnc2VsbGVyX2lkJzogJzAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAw
echo MDAwMDAwMCd9KQogICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwocmVwb25zZS5zdGF0
echo dXNfY29kZSwgNDA0KQogICAgICAgIHNlbGYuYXNzZXJ0SW4oJ2RldGFpbCcsIGpz
echo b24ubG9hZHMocmVwb25zZS5jb250ZW50LmRlY29kZSgndXRmLTgnKSkpCgogICAg
echo ICAgIHJlcG9uc2UgPSBzZWxmLmNsaWVudF9hZG1pbi5nZXQoCiAgICAgICAgICAg
echo IFVSTF9FWFBPUlQsIHsnc3RhcnRfZGF0ZSc6IHNlbGYuZGVidXQsICdlbmRfZGF0
echo ZSc6IHNlbGYuZmluLAogICAgICAgICAgICAgICAgICAgICAgICAgJ3NlbGxlcic6
echo ICdpbmNvbm51QG5leG9yYS5sb2NhbCd9KQogICAgICAgIHNlbGYuYXNzZXJ0RXF1
echo YWwocmVwb25zZS5zdGF0dXNfY29kZSwgNDA0KQoKICAgIGRlZiB0ZXN0X2V4cG9y
echo dF9wZGZfYXZlY19lbWFpbF9leGFjdChzZWxmKToKICAgICAgICByZXBvbnNlID0g
echo c2VsZi5jbGllbnRfYWRtaW4uZ2V0KAogICAgICAgICAgICBVUkxfRVhQT1JULCB7
echo J3N0YXJ0X2RhdGUnOiBzZWxmLmRlYnV0LCAnZW5kX2RhdGUnOiBzZWxmLmZpbiwK
echo ICAgICAgICAgICAgICAgICAgICAgICAgICdzZWxsZXInOiAnYm91YmFjYXIua29u
echo ZUBuZXhvcmEubG9jYWwnfSkKICAgICAgICBzZWxmLmFzc2VydEVxdWFsKHJlcG9u
echo c2Uuc3RhdHVzX2NvZGUsIDIwMCkKICAgICAgICBzZWxmLmFzc2VydEluKCdCb3Vi
echo YWNhcl9Lb25lJywgc2VsZi5fbm9tX2ZpY2hpZXIocmVwb25zZSkpCgogICAgZGVm
echo IHRlc3RfY2Fpc3NpZXJfbGltaXRlX2Ffc29uX3Byb3ByZV9iaWxhbihzZWxmKToK
echo ICAgICAgICAiIiJVbiBjYWlzc2llciBxdWkgZGVtYW5kZSBsZSBiaWxhbiBkJ3Vu
echo IGNvbGzDqGd1ZSBvYnRpZW50IGxlIHNpZW4uIiIiCiAgICAgICAgcmVwb25zZSA9
echo IHNlbGYuY2xpZW50X3ZlbmRldXIxLmdldCgKICAgICAgICAgICAgVVJMX0VYUE9S
echo VCwgeydzdGFydF9kYXRlJzogc2VsZi5kZWJ1dCwgJ2VuZF9kYXRlJzogc2VsZi5m
echo aW4sCiAgICAgICAgICAgICAgICAgICAgICAgICAnc2VsbGVyX2lkJzogc3RyKHNl
echo bGYudmVuZGV1cjIuaWQpfSkKICAgICAgICBzZWxmLmFzc2VydEVxdWFsKHJlcG9u
echo c2Uuc3RhdHVzX2NvZGUsIDIwMCkKICAgICAgICBub20gPSBzZWxmLl9ub21fZmlj
echo aGllcihyZXBvbnNlKQogICAgICAgIHNlbGYuYXNzZXJ0SW4oJ0F3YV9UcmFvcmUn
echo LCBub20pCiAgICAgICAgc2VsZi5hc3NlcnROb3RJbignQm91YmFjYXInLCBub20p
echo CgogICAgZGVmIHRlc3RfZXhwb3J0X3NhbnNfcGFyYW1ldHJlX3JlcG9uZF90b3Vq
echo b3VycyhzZWxmKToKICAgICAgICByZXBvbnNlID0gc2VsZi5jbGllbnRfYWRtaW4u
echo Z2V0KFVSTF9FWFBPUlQsIHsnc3RhcnRfZGF0ZSc6IHNlbGYuZGVidXQsICdlbmRf
echo ZGF0ZSc6IHNlbGYuZmlufSkKICAgICAgICBzZWxmLmFzc2VydEVxdWFsKHJlcG9u
echo c2Uuc3RhdHVzX2NvZGUsIDIwMCkKICAgICAgICBzZWxmLmFzc2VydEluKCdhcHBs
echo aWNhdGlvbi9wZGYnLCByZXBvbnNlWydDb250ZW50LVR5cGUnXSkK
)

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
