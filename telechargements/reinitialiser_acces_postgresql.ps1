# Reinitialisation locale du mot de passe administrateur PostgreSQL.
# A lancer depuis PowerShell en tant qu'administrateur.
# La regle trust temporaire est limitee a la base postgres, au role postgres,
# et a l'adresse locale 127.0.0.1/32. Le pg_hba.conf original est restaure.

$ErrorActionPreference = 'Stop'
$serviceName = 'postgresql-x64-18'
$dataDir = 'C:\Program Files\PostgreSQL\18\data'
$hbaPath = Join-Path $dataDir 'pg_hba.conf'
$psqlPath = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$trustRule = 'host    postgres    postgres    127.0.0.1/32    trust'

function Wait-PgServiceRunning {
    param(
        [string]$Name,
        [int]$TimeoutSeconds = 45
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $current = Get-Service -Name $Name -ErrorAction Stop
        if ($current.Status -eq 'Running') {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    return ((Get-Service -Name $Name -ErrorAction Stop).Status -eq 'Running')
}

function Start-Or-RestartPgService {
    param([string]$Name)
    $current = Get-Service -Name $Name -ErrorAction Stop
    if ($current.Status -eq 'Running') {
        Restart-Service -Name $Name -ErrorAction Stop
    } else {
        Start-Service -Name $Name -ErrorAction Stop
    }
    if (-not (Wait-PgServiceRunning -Name $Name)) {
        throw ('Le service PostgreSQL ne passe pas a l etat Running : ' + $Name)
    }
}

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object -TypeName System.Security.Principal.WindowsPrincipal -ArgumentList $identity
if (-not $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Lancez PowerShell avec l option "Executer en tant qu administrateur", puis relancez le script.'
}

$service = Get-CimInstance Win32_Service -Filter "Name='$serviceName'" -ErrorAction Stop
if (-not $service) {
    throw ('Service Windows introuvable : ' + $serviceName)
}
if ($service.PathName -notlike '*C:\Program Files\PostgreSQL\18\data*') {
    throw 'Le dossier de donnees du service ne correspond pas au diagnostic. Aucun fichier modifie.'
}
if (-not (Test-Path -LiteralPath $hbaPath)) {
    throw ('pg_hba.conf introuvable : ' + $hbaPath)
}
if (-not (Test-Path -LiteralPath $psqlPath)) {
    throw ('psql.exe introuvable : ' + $psqlPath)
}
if ((Get-Service -Name $serviceName).Status -ne 'Running') {
    throw 'Le service PostgreSQL est arrete. Aucun fichier modifie.'
}

$originalBytes = [System.IO.File]::ReadAllBytes($hbaPath)
$originalText = [System.Text.Encoding]::UTF8.GetString($originalBytes)
$expectedRule = '(?im)^\s*host\s+all\s+all\s+127\.0\.0\.1/32\s+scram-sha-256(?:\s|$)'
if ($originalText -notmatch $expectedRule) {
    throw 'Regle SCRAM localhost attendue introuvable. Aucun fichier modifie.'
}
$existingTrustRule = '(?im)^\s*host\s+postgres\s+postgres\s+127\.0\.0\.1/32\s+trust(?:\s|$)'
if ($originalText -match $existingTrustRule) {
    throw 'La regle trust temporaire existe deja. Verifiez pg_hba.conf; aucune modification.'
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupPath = Join-Path $dataDir ('pg_hba.conf.nexora-reset-' + $stamp + '.bak')
[System.IO.File]::Copy($hbaPath, $backupPath, $false)
Write-Output ('Copie de pg_hba.conf original : ' + $backupPath)
Write-Output 'Ce script ne modifie pas le contenu des bases.'
Write-Warning 'Pendant un court instant, les processus locaux pourront se connecter sans mot de passe comme postgres a la base postgres.'
Write-Warning 'Fermez les autres clients locaux et gardez cette fenetre PowerShell ouverte jusqu a la fin.'

$trustInstalled = $false
$resetSessionExitCode = $null
$restoreSucceeded = $false
try {
    $ruleBytes = [System.Text.Encoding]::ASCII.GetBytes($trustRule + "`r`n")
    $bomLength = 0
    if ($originalBytes.Length -ge 3 -and $originalBytes[0] -eq 0xEF -and $originalBytes[1] -eq 0xBB -and $originalBytes[2] -eq 0xBF) {
        $bomLength = 3
    }

    $temporaryBytes = [System.Array]::CreateInstance([byte], ($originalBytes.Length + $ruleBytes.Length))
    if ($bomLength -gt 0) {
        [System.Array]::Copy($originalBytes, 0, $temporaryBytes, 0, $bomLength)
    }
    [System.Array]::Copy($ruleBytes, 0, $temporaryBytes, $bomLength, $ruleBytes.Length)
    [System.Array]::Copy(
        $originalBytes,
        $bomLength,
        $temporaryBytes,
        ($bomLength + $ruleBytes.Length),
        ($originalBytes.Length - $bomLength)
    )

    $trustInstalled = $true
    [System.IO.File]::WriteAllBytes($hbaPath, $temporaryBytes)
    Start-Or-RestartPgService -Name $serviceName

    Write-Output ''
    Write-Output 'Acces temporaire limite a localhost / role postgres / base postgres.'
    Write-Output 'A postgres=#, tapez : SET password_encryption = ''scram-sha-256'';'
    Write-Output 'Puis tapez : \password postgres'
    Write-Output 'Saisissez le nouveau mot de passe deux fois. Rien ne sera affiche pendant la saisie.'
    Write-Output 'Enfin, tapez : \q'
    Write-Output ''

    & $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres'
    $resetSessionExitCode = $LASTEXITCODE
    if ($resetSessionExitCode -ne 0) {
        throw ('Code retour psql non nul : ' + $resetSessionExitCode)
    }
} finally {
    if ($trustInstalled) {
        try {
            $savedBytes = [System.IO.File]::ReadAllBytes($backupPath)
            [System.IO.File]::WriteAllBytes($hbaPath, $savedBytes)
            Start-Or-RestartPgService -Name $serviceName
            $restoreSucceeded = $true
            Write-Output ''
            Write-Output 'pg_hba.conf original restaure et PostgreSQL redemarre.'
        } catch {
            Write-Warning ('ECHEC DE RESTAURATION AUTOMATIQUE : ' + $_.Exception.Message)
            Write-Warning ('Conservez cette copie : ' + $backupPath)
            Write-Warning 'Le fichier original doit etre restaure avant de laisser PostgreSQL accessible.'
        }
    }
}

if (-not $restoreSucceeded) {
    throw ('Restauration de pg_hba.conf non confirmee. Copie de secours : ' + $backupPath)
}

Write-Output ''
Write-Output 'Verifiez le nouveau mot de passe postgres a l invite. La saisie restera invisible.'
& $psqlPath -X -h '127.0.0.1' -p '5432' -U 'postgres' -d 'postgres' -W -c 'SELECT current_user, current_database();'
$verifyExitCode = $LASTEXITCODE
Write-Output ('Code retour de verification=' + $verifyExitCode)
if ($verifyExitCode -eq 0) {
    Write-Output 'Acces administrateur PostgreSQL confirme; authentification SCRAM originale active.'
} else {
    Write-Warning 'La verification du mot de passe a echoue. Le pg_hba.conf original est restaure.'
}
