# Migration NEXORA de SQLite vers PostgreSQL 18.
# A executer depuis PowerShell Windows, avec le projet sur D:\NEXORA.
# Les mots de passe sont saisis localement, jamais affiches ni inscrits dans ce script.
# La base SQLite source reste intacte; une copie SQLite verifiee et un fixture JSON sont conserves.

$ErrorActionPreference = 'Continue'
$project = 'D:\NEXORA'
$serviceName = 'postgresql-x64-18'
$psqlPath = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$hbaPath = 'C:\Program Files\PostgreSQL\18\data\pg_hba.conf'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$backupPath = Join-Path $project ('db.sqlite3.pre-postgresql-' + $stamp + '.bak')
$fixturePath = Join-Path $project ('sqlite_pre_postgresql_' + $stamp + '.json')
$verifyPath = Join-Path $project ('postgresql_verification_' + $stamp + '.json')

$environmentNames = @(
    'DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT',
    'PGPASSWORD', 'PYTHONUTF8', 'NEXORA_SOURCE_DB', 'NEXORA_BACKUP_PATH', 'NEXORA_FIXTURE_PATH',
    'NEXORA_FIXTURE_BEFORE', 'NEXORA_FIXTURE_AFTER'
)
$oldEnvironment = @{}
foreach ($name in $environmentNames) {
    $oldEnvironment[$name] = [System.Environment]::GetEnvironmentVariable($name, 'Process')
}

$migrationSucceeded = $false
$migrationPhaseStarted = $false
$roleCreatedByScript = $false
$databaseCreatedByScript = $false
$adminSecure = $null
$appSecure = $null
$adminPointer = [IntPtr]::Zero
$appPointer = [IntPtr]::Zero
$adminPasswordPlain = $null
$appPasswordPlain = $null

function Restore-ProcessEnvironmentValue {
    param([string]$Name, [string]$Value)
    if ($null -eq $Value) {
        Remove-Item -LiteralPath ('Env:' + $Name) -ErrorAction SilentlyContinue
    } else {
        [System.Environment]::SetEnvironmentVariable($Name, $Value, 'Process')
    }
}

try {
    if (-not (Test-Path -LiteralPath (Join-Path $project 'manage.py'))) {
        throw ('manage.py introuvable dans ' + $project)
    }
    if (-not (Test-Path -LiteralPath (Join-Path $project 'db.sqlite3'))) {
        throw 'La base SQLite D:\NEXORA\db.sqlite3 est introuvable.'
    }
    foreach ($artifactPath in @($backupPath, $fixturePath, $verifyPath)) {
        if (Test-Path -LiteralPath $artifactPath) {
            throw ('Le fichier de sortie existe deja; aucun fichier ne sera ecrase : ' + $artifactPath)
        }
    }
    if (-not (Test-Path -LiteralPath $psqlPath)) {
        throw ('psql.exe introuvable : ' + $psqlPath)
    }
    if ((Get-Service -Name $serviceName -ErrorAction Stop).Status -ne 'Running') {
        throw 'Le service PostgreSQL doit etre Running avant la migration.'
    }
    if (-not (Test-Path -LiteralPath $hbaPath)) {
        throw ('pg_hba.conf introuvable : ' + $hbaPath)
    }
    $hbaTrust = Select-String -Path $hbaPath -Pattern '^\s*host\s+postgres\s+postgres\s+127\.0\.0\.1/32\s+trust(?:\s|$)' -Quiet -ErrorAction Stop
    if ($hbaTrust) {
        throw 'Une regle trust temporaire est encore active. Ne migrez pas; restaurez pg_hba.conf.'
    }

    Set-Location -LiteralPath $project -ErrorAction Stop
    Write-Output 'Cette operation conserve SQLite et transfere ses donnees dans une nouvelle base PostgreSQL.'
    Write-Output 'Arretez le serveur Django et toute activite sur l application avant de continuer.'
    $confirmation = Read-Host 'Tapez ARRETE si le serveur Django est arrete'
    if ($confirmation -cne 'ARRETE') {
        throw 'Migration annulee : le serveur Django doit etre arrete.'
    }

    Write-Output ''
    Write-Output '=== 1. Copie coherente et verification de SQLite ==='
    $oldSourceEnvironment = [System.Environment]::GetEnvironmentVariable('NEXORA_SOURCE_DB', 'Process')
    $oldBackupEnvironment = [System.Environment]::GetEnvironmentVariable('NEXORA_BACKUP_PATH', 'Process')
    $env:NEXORA_SOURCE_DB = Join-Path $project 'db.sqlite3'
    $env:NEXORA_BACKUP_PATH = $backupPath
    $backupOutput = & py -c "import os, sqlite3; source=sqlite3.connect(os.environ['NEXORA_SOURCE_DB']); destination=sqlite3.connect(os.environ['NEXORA_BACKUP_PATH']); source.backup(destination); result=destination.execute('PRAGMA integrity_check').fetchone()[0]; print('INTEGRITE_SQLITE=' + str(result)); destination.close(); source.close()"
    $backupExitCode = $LASTEXITCODE
    Restore-ProcessEnvironmentValue -Name 'NEXORA_SOURCE_DB' -Value $oldSourceEnvironment
    Restore-ProcessEnvironmentValue -Name 'NEXORA_BACKUP_PATH' -Value $oldBackupEnvironment
    $backupOutput | ForEach-Object { Write-Output $_ }
    if ($backupExitCode -ne 0 -or (($backupOutput -join '') -notmatch 'INTEGRITE_SQLITE=ok')) {
        throw 'La copie SQLite n a pas passe integrity_check. Aucune migration lancee.'
    }
    Get-Item -LiteralPath $backupPath -ErrorAction Stop | Select-Object FullName, Length

    Write-Output ''
    Write-Output '=== 2. Export complet des donnees SQLite ==='
    $oldEngine = [System.Environment]::GetEnvironmentVariable('DB_ENGINE', 'Process')
    $oldPythonUtf8 = [System.Environment]::GetEnvironmentVariable('PYTHONUTF8', 'Process')
    $env:DB_ENGINE = 'sqlite'
    $env:PYTHONUTF8 = '1'
    try {
        & py manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --exclude sessions --indent 2 --output $fixturePath
        $dumpExitCode = $LASTEXITCODE
    } finally {
        Restore-ProcessEnvironmentValue -Name 'DB_ENGINE' -Value $oldEngine
        Restore-ProcessEnvironmentValue -Name 'PYTHONUTF8' -Value $oldPythonUtf8
    }
    if ($dumpExitCode -ne 0 -or -not (Test-Path -LiteralPath $fixturePath)) {
        throw 'dumpdata SQLite a echoue. La base source reste inchangee.'
    }

    $oldFixtureEnvironment = [System.Environment]::GetEnvironmentVariable('NEXORA_FIXTURE_PATH', 'Process')
    $env:NEXORA_FIXTURE_PATH = $fixturePath
    $fixtureCountOutput = & py -c "import json, os; data=json.load(open(os.environ['NEXORA_FIXTURE_PATH'], encoding='utf-8')); print(len(data))"
    $fixtureCountExitCode = $LASTEXITCODE
    Restore-ProcessEnvironmentValue -Name 'NEXORA_FIXTURE_PATH' -Value $oldFixtureEnvironment
    if ($fixtureCountExitCode -ne 0) {
        throw 'Le fichier fixture JSON ne peut pas etre lu. La base source reste inchangee.'
    }
    $fixtureCountText = ($fixtureCountOutput -join '').Trim()
    $fixtureCount = 0
    if (-not [int]::TryParse($fixtureCountText, [ref]$fixtureCount) -or $fixtureCount -lt 1) {
        throw 'L export JSON est vide ou invalide. La base source reste inchangee.'
    }
    Write-Output ('Enregistrements exportes : ' + $fixtureCount)
    Write-Output ('Fixture conserve : ' + $fixturePath)
    Write-Warning 'Le fixture contient les donnees de l application. Ne le partagez pas et ne le commitez pas.'

    Write-Output ''
    Write-Output '=== 3. Connexion administrateur et creation du role/base ==='
    $adminSecure = Read-Host 'Mot de passe administrateur PostgreSQL postgres (saisie masquee)' -AsSecureString
    if ($null -eq $adminSecure -or $adminSecure.Length -eq 0) {
        throw 'Mot de passe administrateur vide; migration arretee.'
    }
    $adminPointer = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminSecure)
    $adminPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($adminPointer)
    $env:PGPASSWORD = $adminPasswordPlain

    $adminCheck = & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -tAc 'SELECT current_user;'
    $adminCheckCode = $LASTEXITCODE
    if ($adminCheckCode -ne 0 -or (($adminCheck -join '').Trim() -ne 'postgres')) {
        throw 'Connexion administrateur PostgreSQL refusee. Aucune table ni donnee migree.'
    }

    $roleExistsOutput = & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -tAc "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nexora');"
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de verifier les roles PostgreSQL.' }
    $dbExistsOutput = & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -tAc "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'nexora_db');"
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de verifier les bases PostgreSQL.' }
    $roleExists = (($roleExistsOutput -join '').Trim() -eq 't')
    $dbExists = (($dbExistsOutput -join '').Trim() -eq 't')
    if ($roleExists -or $dbExists) {
        throw 'Le role nexora ou la base nexora_db existe deja. Arret sans ecrasement; communiquez ce resultat.'
    }

    $appSecure = Read-Host 'Choisissez le mot de passe du role nexora (saisie masquee, ASCII)' -AsSecureString
    if ($null -eq $appSecure -or $appSecure.Length -eq 0) {
        throw 'Mot de passe du role nexora vide; migration arretee avant creation du role/base.'
    }
    $appPointer = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($appSecure)
    $appPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($appPointer)
    if ($appPasswordPlain -ceq $adminPasswordPlain) {
        throw 'Choisissez un mot de passe applicatif distinct de celui de postgres.'
    }

    & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -c 'CREATE ROLE nexora WITH LOGIN;'
    if ($LASTEXITCODE -ne 0) { throw 'Creation du role nexora echouee.' }
    $roleCreatedByScript = $true
    & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -c "CREATE DATABASE nexora_db WITH OWNER = nexora ENCODING = 'UTF8' TEMPLATE = template0;"
    if ($LASTEXITCODE -ne 0) {
        & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -c 'DROP ROLE IF EXISTS nexora;'
        if ($LASTEXITCODE -eq 0) { $roleCreatedByScript = $false }
        throw 'Creation de nexora_db echouee; role temporaire retire si possible.'
    }
    $databaseCreatedByScript = $true

    Write-Output 'Configurez le mot de passe que vous venez de choisir pour le role applicatif nexora.'
    Write-Output 'A postgres=#, tapez : SET password_encryption = ''scram-sha-256'';'
    Write-Output 'Puis : \password nexora'
    Write-Output 'Saisissez exactement ce meme mot de passe deux fois, puis tapez : \q'
    & $psqlPath -X -v ON_ERROR_STOP=1 -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres'
    $appRolePsqlExitCode = $LASTEXITCODE
    Restore-ProcessEnvironmentValue -Name 'PGPASSWORD' -Value $oldEnvironment['PGPASSWORD']
    if ($appRolePsqlExitCode -ne 0) {
        throw ('Configuration du role applicatif interrompue (code ' + $appRolePsqlExitCode + '). SQLite reste intacte.')
    }

    $env:DB_ENGINE = 'postgresql'
    $env:DB_NAME = 'nexora_db'
    $env:DB_USER = 'nexora'
    $env:DB_PASSWORD = $appPasswordPlain
    $env:DB_HOST = '127.0.0.1'
    $env:DB_PORT = '5432'

    Write-Output ''
    Write-Output '=== 4. Test de connexion Django vers PostgreSQL ==='
    & py manage.py shell -c "from django.db import connection; connection.ensure_connection(); cursor=connection.cursor(); cursor.execute('SELECT current_user, current_database()'); user, name=cursor.fetchone(); assert connection.vendor == 'postgresql' and user == 'nexora' and name == 'nexora_db', (connection.vendor, user, name); print('CONNEXION=' + connection.vendor); print('UTILISATEUR=' + user); print('BASE=' + name)"
    if ($LASTEXITCODE -ne 0) {
        throw 'Django ne se connecte pas a nexora_db. Aucune donnee SQLite n a ete chargee.'
    }

    Write-Output ''
    Write-Output '=== 5. Creation du schema PostgreSQL ==='
    $migrationPhaseStarted = $true
    & py manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Les migrations Django PostgreSQL ont echoue. SQLite reste intacte.' }

    Write-Output ''
    Write-Output '=== 6. Import des donnees SQLite ==='
    $oldPythonUtf8 = [System.Environment]::GetEnvironmentVariable('PYTHONUTF8', 'Process')
    $env:PYTHONUTF8 = '1'
    try {
        & py manage.py loaddata $fixturePath
        $loadExitCode = $LASTEXITCODE
    } finally {
        Restore-ProcessEnvironmentValue -Name 'PYTHONUTF8' -Value $oldPythonUtf8
    }
    if ($loadExitCode -ne 0) { throw 'loaddata a echoue. SQLite et sa copie de secours restent intactes.' }

    Write-Output ''
    Write-Output '=== 7. Verification Django et comparaison des objets ==='
    & py manage.py check --database default
    if ($LASTEXITCODE -ne 0) { throw 'manage.py check a echoue sur PostgreSQL.' }

    $oldPythonUtf8 = [System.Environment]::GetEnvironmentVariable('PYTHONUTF8', 'Process')
    $env:PYTHONUTF8 = '1'
    try {
        & py manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --exclude sessions --indent 2 --output $verifyPath
        $verifyDumpExitCode = $LASTEXITCODE
    } finally {
        Restore-ProcessEnvironmentValue -Name 'PYTHONUTF8' -Value $oldPythonUtf8
    }
    if ($verifyDumpExitCode -ne 0 -or -not (Test-Path -LiteralPath $verifyPath)) {
        throw 'Impossible de re-exporter les donnees PostgreSQL pour comparaison.'
    }
    $oldBeforeEnvironment = [System.Environment]::GetEnvironmentVariable('NEXORA_FIXTURE_BEFORE', 'Process')
    $oldAfterEnvironment = [System.Environment]::GetEnvironmentVariable('NEXORA_FIXTURE_AFTER', 'Process')
    $env:NEXORA_FIXTURE_BEFORE = $fixturePath
    $env:NEXORA_FIXTURE_AFTER = $verifyPath
    $compareCode = "import collections, hashlib, json, os; a=json.load(open(os.environ['NEXORA_FIXTURE_BEFORE'], encoding='utf-8')); b=json.load(open(os.environ['NEXORA_FIXTURE_AFTER'], encoding='utf-8')); ca=sorted((x['model'], json.dumps(x.get('pk'), sort_keys=True), json.dumps(x['fields'], sort_keys=True, separators=(',', ':'))) for x in a); cb=sorted((x['model'], json.dumps(x.get('pk'), sort_keys=True), json.dumps(x['fields'], sort_keys=True, separators=(',', ':'))) for x in b); ac=collections.Counter(x[0] for x in ca); bc=collections.Counter(x[0] for x in cb); print('OBJETS_SQLITE=' + str(len(a))); print('OBJETS_POSTGRESQL=' + str(len(b))); [print('ECART ' + k + ': SQLite=' + str(ac[k]) + ', PostgreSQL=' + str(bc[k])) for k in sorted(set(ac) | set(bc)) if ac[k] != bc[k]]; ah=hashlib.sha256(json.dumps(ca, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest(); bh=hashlib.sha256(json.dumps(cb, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest(); print('SHA256_SQLITE=' + ah); print('SHA256_POSTGRESQL=' + bh); print('COMPARAISON_COMPLETE=' + ('IDENTIQUE' if ca == cb else 'DIFFERENTE')); raise SystemExit(0 if ca == cb else 2)"
    $compareOutput = & py -c $compareCode
    $compareExitCode = $LASTEXITCODE
    Restore-ProcessEnvironmentValue -Name 'NEXORA_FIXTURE_BEFORE' -Value $oldBeforeEnvironment
    Restore-ProcessEnvironmentValue -Name 'NEXORA_FIXTURE_AFTER' -Value $oldAfterEnvironment
    $compareOutput | ForEach-Object { Write-Output $_ }
    if ($compareExitCode -ne 0) { throw 'La comparaison complete des donnees SQLite/PostgreSQL differe; SQLite reste intacte.' }

    & py manage.py audit_production
    if ($LASTEXITCODE -ne 0) { throw 'audit_production a echoue apres la migration.' }

    $migrationSucceeded = $true
    Write-Output ''
    Write-Output 'MIGRATION TERMINEE. DB_ENGINE=postgresql reste defini dans cette fenetre PowerShell uniquement.'
    Write-Output 'Pour tester dans cette fenetre : Set-Location D:\NEXORA; py manage.py runserver 0.0.0.0:8000'
    Write-Output ('Copie SQLite : ' + $backupPath)
    Write-Output ('Fixture source conserve : ' + $fixturePath)
} finally {
    if (-not $migrationSucceeded -and -not $migrationPhaseStarted -and ($roleCreatedByScript -or $databaseCreatedByScript) -and $null -ne $adminPasswordPlain) {
        Write-Warning 'Echec avant les migrations Django : tentative de suppression de la base et du role vides crees par ce script.'
        $env:PGPASSWORD = $adminPasswordPlain
        $databaseRemoved = -not $databaseCreatedByScript
        if ($databaseCreatedByScript) {
            & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -c 'DROP DATABASE IF EXISTS nexora_db WITH (FORCE);'
            $databaseRemoved = ($LASTEXITCODE -eq 0)
            if ($databaseRemoved) { $databaseCreatedByScript = $false }
        }
        if ($roleCreatedByScript -and $databaseRemoved) {
            & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -c 'DROP ROLE IF EXISTS nexora;'
            $roleCreatedByScript = ($LASTEXITCODE -ne 0)
        }
        if (-not $databaseRemoved -or $roleCreatedByScript) {
            Write-Warning 'Nettoyage PostgreSQL incomplet; ne relancez pas le script avant d examiner les roles et bases.'
        } else {
            Write-Output 'Role/base de pre-migration nettoyes; vous pourrez relancer le script apres correction de l erreur.'
        }
    }
    Restore-ProcessEnvironmentValue -Name 'PGPASSWORD' -Value $oldEnvironment['PGPASSWORD']
    Restore-ProcessEnvironmentValue -Name 'PYTHONUTF8' -Value $oldEnvironment['PYTHONUTF8']
    Restore-ProcessEnvironmentValue -Name 'NEXORA_SOURCE_DB' -Value $oldEnvironment['NEXORA_SOURCE_DB']
    Restore-ProcessEnvironmentValue -Name 'NEXORA_BACKUP_PATH' -Value $oldEnvironment['NEXORA_BACKUP_PATH']
    Restore-ProcessEnvironmentValue -Name 'NEXORA_FIXTURE_PATH' -Value $oldEnvironment['NEXORA_FIXTURE_PATH']
    Restore-ProcessEnvironmentValue -Name 'NEXORA_FIXTURE_BEFORE' -Value $oldEnvironment['NEXORA_FIXTURE_BEFORE']
    Restore-ProcessEnvironmentValue -Name 'NEXORA_FIXTURE_AFTER' -Value $oldEnvironment['NEXORA_FIXTURE_AFTER']
    if ($migrationSucceeded -and (Test-Path -LiteralPath $verifyPath)) {
        Remove-Item -LiteralPath $verifyPath -Force -ErrorAction SilentlyContinue
    }
    if (-not $migrationSucceeded) {
        foreach ($name in @('DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT')) {
            Restore-ProcessEnvironmentValue -Name $name -Value $oldEnvironment[$name]
        }
        if ($migrationPhaseStarted) {
            Write-Warning 'SQLite reste intacte. Le schema ou les donnees PostgreSQL peuvent etre partiels; ne relancez pas sans examiner la sortie.'
        } elseif ($roleCreatedByScript -or $databaseCreatedByScript) {
            Write-Warning 'SQLite reste intacte. Un role ou une base PostgreSQL peut rester; ne relancez pas sans examiner la sortie.'
        } else {
            Write-Warning 'SQLite reste intacte et aucune donnee n a ete importee. Corrigez l erreur avant de relancer.'
        }
    }
    if ($adminPointer -ne [IntPtr]::Zero) {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($adminPointer)
    }
    if ($appPointer -ne [IntPtr]::Zero) {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($appPointer)
    }
    if ($null -ne $adminSecure) { $adminSecure.Dispose() }
    if ($null -ne $appSecure) { $appSecure.Dispose() }
    $adminPasswordPlain = $null
    $appPasswordPlain = $null
}
