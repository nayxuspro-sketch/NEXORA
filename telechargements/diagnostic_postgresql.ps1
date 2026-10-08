# Diagnostic PostgreSQL NEXORA - lecture seule
# Ne modifie ni settings.py, ni la base SQLite, ni le service PostgreSQL.
# Aucun mot de passe ni SECRET_KEY n'est affiche.

$ErrorActionPreference = 'Continue'
$project = 'D:\NEXORA'

if (-not (Test-Path -LiteralPath $project)) {
    Write-Output ('ERREUR: dossier du projet introuvable: ' + $project)
    exit 1
}
Set-Location -LiteralPath $project

Write-Output '============================================================'
Write-Output 'DIAGNOSTIC PRE-MIGRATION POSTGRESQL - NEXORA (LECTURE SEULE)'
Write-Output ('Projet: ' + (Get-Location).Path)
Write-Output 'Aucun secret ne doit etre communique; le script les masque.'
Write-Output '============================================================'

Write-Output ''
Write-Output '=== 1. Versions Python, Django et pilote PostgreSQL ==='
py --version
py manage.py --version
py -c "import importlib.util as u; print('psycopg3=' + str(u.find_spec('psycopg') is not None)); print('psycopg2=' + str(u.find_spec('psycopg2') is not None))"

Write-Output ''
Write-Output '=== 2. Configuration Django active (sans identifiants) ==='
py manage.py shell -c "import os, importlib.util; from django.conf import settings; d=settings.DATABASES['default']; m=os.environ.get('DJANGO_SETTINGS_MODULE',''); spec=importlib.util.find_spec(m) if m else None; n=str(d.get('NAME','')); n='<masque: URL configuree>' if '://' in n else n; print('SETTINGS_MODULE=' + (m or '<absent>')); print('SETTINGS_FILE=' + (spec.origin if spec else '<non trouve>')); print('ENGINE=' + str(d.get('ENGINE',''))); print('NAME=' + n); print('HOST=' + str(d.get('HOST',''))); print('PORT=' + str(d.get('PORT',''))); print('CONN_MAX_AGE=' + str(d.get('CONN_MAX_AGE',0))); print('ATOMIC_REQUESTS=' + str(d.get('ATOMIC_REQUESTS',False))); print('USE_TZ=' + str(settings.USE_TZ)); print('TIME_ZONE=' + str(settings.TIME_ZONE)); print('MEDIA_ROOT=' + str(getattr(settings,'MEDIA_ROOT',''))); print('DB_USER=<non affiche>'); print('DB_PASSWORD=<non affiche>'); print('SECRET_KEY=<non affiche>')"

Write-Output ''
Write-Output '=== 3. Etat local de PostgreSQL ==='
$pgServices = @(Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue)
if ($pgServices.Count -gt 0) {
    $pgServices | Select-Object Name, Status | Format-Table -AutoSize
} else {
    Write-Output 'Aucun service Windows nomme postgresql* trouve.'
}

$psql = Get-Command 'psql' -ErrorAction SilentlyContinue
if ($psql) {
    Write-Output ('PSQL_PATH=' + $psql.Source)
    & $psql.Source --version
} else {
    Write-Output 'PSQL_PATH=<absent du PATH>'
}

$pgRoot = Join-Path $env:ProgramFiles 'PostgreSQL'
if (Test-Path -LiteralPath $pgRoot) {
    Write-Output ('Dossiers PostgreSQL installes sous ' + $pgRoot + ':')
    Get-ChildItem -LiteralPath $pgRoot -Directory -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName
} else {
    Write-Output 'Aucun dossier PostgreSQL trouve sous Program Files.'
}

$tnc = Get-Command 'Test-NetConnection' -ErrorAction SilentlyContinue
if ($tnc) {
    $port5432 = Test-NetConnection -ComputerName '127.0.0.1' -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue
    Write-Output ('TCP 127.0.0.1:5432 accessible=' + [string]$port5432)
} else {
    Write-Output 'Test-NetConnection indisponible; le port 5432 n a pas ete teste.'
}

Write-Output ''
Write-Output '=== 4. Fichiers de dependances presents (noms seulement) ==='
$dependencyFiles = @('requirements.txt', 'requirements-prod.txt', 'pyproject.toml', 'Pipfile') |
    Where-Object { Test-Path -LiteralPath (Join-Path $project $_) }
if ($dependencyFiles.Count -gt 0) {
    $dependencyFiles | ForEach-Object { Write-Output $_ }
} else {
    Write-Output 'Aucun fichier de dependances courant trouve a la racine.'
}

Write-Output ''
Write-Output '=== 5. Etat des migrations Django (lecture seule) ==='
py manage.py showmigrations --plan

Write-Output ''
Write-Output '=== FIN DU DIAGNOSTIC ==='
Write-Output 'Collez la sortie complete. Elle ne contient ni mot de passe ni SECRET_KEY.'
