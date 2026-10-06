# Sauvegarde logique locale de NEXORA (PostgreSQL).
# Lecture seule : ne modifie ni la base, ni les migrations, ni settings.py.
# Le mot de passe est demande masque et passe a pg_dump via l'environnement du processus.

$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$serviceName = 'postgresql-x64-18'
$backupDirectory = Join-Path $project 'sauvegardes-postgresql'
$temporaryPath = $null
$exitCode = 0
$environmentNames = @('PGPASSWORD', 'PGCONNECT_TIMEOUT')
$oldEnvironment = @{}
foreach ($name in $environmentNames) {
    $oldEnvironment[$name] = [System.Environment]::GetEnvironmentVariable($name, 'Process')
}

try {
    if (-not (Test-Path -LiteralPath (Join-Path $project 'manage.py'))) {
        throw ('manage.py introuvable dans ' + $project + '. Placez les fichiers dans D:\NEXORA.')
    }

    $service = Get-Service -Name $serviceName -ErrorAction Stop
    if ($service.Status -ne 'Running') {
        throw ('Le service PostgreSQL doit etre demarre : ' + $serviceName)
    }

    $pgBin = Join-Path $env:ProgramFiles 'PostgreSQL\18\bin'
    $pgDump = Join-Path $pgBin 'pg_dump.exe'
    if (-not (Test-Path -LiteralPath $pgDump)) {
        $foundPgDump = Get-Command 'pg_dump.exe' -ErrorAction SilentlyContinue
        if ($foundPgDump) {
            $pgDump = $foundPgDump.Source
        }
    }
    if (-not (Test-Path -LiteralPath $pgDump)) {
        throw 'pg_dump.exe introuvable. Verifiez l installation PostgreSQL 18.'
    }

    $pgRestore = Join-Path (Split-Path -Parent $pgDump) 'pg_restore.exe'
    if (-not (Test-Path -LiteralPath $pgRestore)) {
        $foundPgRestore = Get-Command 'pg_restore.exe' -ErrorAction SilentlyContinue
        if ($foundPgRestore) {
            $pgRestore = $foundPgRestore.Source
        }
    }
    if (-not (Test-Path -LiteralPath $pgRestore)) {
        throw 'pg_restore.exe introuvable a cote de pg_dump.exe.'
    }

    $pgDumpVersionOutput = & $pgDump --version 2>&1
    $pgDumpVersionExit = $LASTEXITCODE
    $pgDumpVersion = ($pgDumpVersionOutput | Out-String).Trim()
    if ($pgDumpVersionExit -ne 0 -or $pgDumpVersion -notmatch 'pg_dump \(PostgreSQL\) 18(\.|$)') {
        throw ('pg_dump version 18 est requis. Version detectee : ' + $pgDumpVersion)
    }

    $pgRestoreVersionOutput = & $pgRestore --version 2>&1
    $pgRestoreVersionExit = $LASTEXITCODE
    $pgRestoreVersion = ($pgRestoreVersionOutput | Out-String).Trim()
    if ($pgRestoreVersionExit -ne 0 -or $pgRestoreVersion -notmatch 'pg_restore \(PostgreSQL\) 18(\.|$)') {
        throw ('pg_restore version 18 est requis. Version detectee : ' + $pgRestoreVersion)
    }

    $secret = Read-Host 'Mot de passe applicatif du role nexora (saisie masquee)' -AsSecureString
    if ($null -eq $secret -or $secret.Length -eq 0) {
        throw 'Le mot de passe applicatif est vide.'
    }

    $pointer = [System.IntPtr]::Zero
    try {
        $pointer = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        $env:PGPASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    } finally {
        if ($pointer -ne [System.IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        }
        $secret.Dispose()
    }
    $env:PGCONNECT_TIMEOUT = '10'

    if (-not (Test-Path -LiteralPath $backupDirectory)) {
        New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
    }

    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
    $baseName = 'nexora_db_' + $stamp
    $finalPath = Join-Path $backupDirectory ($baseName + '.dump')
    $temporaryPath = Join-Path $backupDirectory ($baseName + '.partial')
    if ((Test-Path -LiteralPath $finalPath) -or (Test-Path -LiteralPath $temporaryPath)) {
        throw 'Un fichier de sauvegarde de meme nom existe deja. Relancez le script.'
    }

    Write-Output 'Creation de la sauvegarde PostgreSQL (base nexora_db)...'
    $dumpArguments = @(
        '--format=custom',
        '--no-owner',
        '--no-privileges',
        '--no-password',
        '--host=127.0.0.1',
        '--port=5432',
        '--username=nexora',
        '--dbname=nexora_db',
        '--file',
        $temporaryPath
    )
    $dumpOutput = & $pgDump @dumpArguments 2>&1
    $dumpExitCode = $LASTEXITCODE
    if ($dumpOutput) {
        $dumpOutput | ForEach-Object { Write-Output ([string]$_) }
    }
    if ($dumpExitCode -ne 0) {
        throw ('pg_dump a echoue avec le code ' + $dumpExitCode + '.')
    }
    if (-not (Test-Path -LiteralPath $temporaryPath) -or (Get-Item -LiteralPath $temporaryPath).Length -le 0) {
        throw 'pg_dump n a pas produit une archive non vide.'
    }

    Write-Output 'Verification de lisibilite avec pg_restore --list...'
    $listOutput = & $pgRestore --list $temporaryPath 2>&1
    $listExitCode = $LASTEXITCODE
    $listText = ($listOutput | Out-String).Trim()
    if ($listExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($listText)) {
        throw 'pg_restore ne parvient pas a lire l archive produite.'
    }

    Move-Item -LiteralPath $temporaryPath -Destination $finalPath -ErrorAction Stop
    $temporaryPath = $null
    $backup = Get-Item -LiteralPath $finalPath
    $hash = Get-FileHash -LiteralPath $finalPath -Algorithm SHA256

    Write-Output ''
    Write-Output 'SAUVEGARDE_OK'
    Write-Output ('Fichier : ' + $finalPath)
    Write-Output ('Taille : ' + $backup.Length + ' octets')
    Write-Output ('SHA-256 : ' + $hash.Hash)
    Write-Output 'L archive est lisible; aucune restauration complete n a encore ete testee.'
    Write-Output 'Copiez-la aussi vers un disque externe ou un NAS securise.'
} catch {
    Write-Output ('ECHEC : ' + $_.Exception.Message)
    if ($temporaryPath -and (Test-Path -LiteralPath $temporaryPath)) {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
    }
    $exitCode = 1
} finally {
    foreach ($name in $environmentNames) {
        if ($null -eq $oldEnvironment[$name]) {
            Remove-Item -LiteralPath ('Env:' + $name) -ErrorAction SilentlyContinue
        } else {
            [System.Environment]::SetEnvironmentVariable($name, $oldEnvironment[$name], 'Process')
        }
    }
}

exit $exitCode
