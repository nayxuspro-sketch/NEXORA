# Lancement local de NEXORA avec la base PostgreSQL deja migree.
# Ce script ne lance ni pip install ni migrate et n'ecrit aucun secret sur disque.
# Le mot de passe applicatif est demande de facon masquee a chaque lancement.

$ErrorActionPreference = 'Continue'
$project = $PSScriptRoot
$manage = Join-Path $project 'manage.py'
$serviceName = 'postgresql-x64-18'
$environmentNames = @('DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'NEXORA_ENVIRONMENT')
$oldEnvironment = @{}
foreach ($name in $environmentNames) {
    $oldEnvironment[$name] = [System.Environment]::GetEnvironmentVariable($name, 'Process')
}

try {
    if (-not (Test-Path -LiteralPath $manage)) {
        throw ('manage.py introuvable dans ' + $project)
    }

    $service = Get-Service -Name $serviceName -ErrorAction Stop
    if ($service.Status -ne 'Running') {
        throw ('Le service PostgreSQL doit etre demarre : ' + $serviceName)
    }

    Set-Location -LiteralPath $project -ErrorAction Stop

    $env:DB_ENGINE = 'postgresql'
    $env:DB_NAME = 'nexora_db'
    $env:DB_USER = 'nexora'
    $env:DB_HOST = '127.0.0.1'
    $env:DB_PORT = '5432'
    $env:NEXORA_ENVIRONMENT = 'development'

    $secret = Read-Host 'Mot de passe applicatif du role nexora (saisie masquee)' -AsSecureString
    if ($null -eq $secret -or $secret.Length -eq 0) {
        throw 'Le mot de passe applicatif est vide.'
    }

    $pointer = [System.IntPtr]::Zero
    try {
        $pointer = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        $env:DB_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    } finally {
        if ($pointer -ne [System.IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        }
        $secret.Dispose()
    }

    Write-Output '=== Verification de la connexion PostgreSQL ==='
    & py $manage shell -c "from django.db import connection; c=connection.cursor(); c.execute('SELECT current_user,current_database()'); user,db=c.fetchone(); assert connection.vendor == 'postgresql' and (user,db)==('nexora','nexora_db'), (connection.vendor,user,db); print('POSTGRESQL_OK',user,db)"
    if ($LASTEXITCODE -ne 0) {
        throw 'Connexion PostgreSQL echouee. Le serveur Django ne sera pas lance.'
    }

    & py $manage check
    if ($LASTEXITCODE -ne 0) {
        throw 'Le controle Django a echoue. Le serveur ne sera pas lance.'
    }

    Write-Output ''
    Write-Output 'NEXORA demarre sur PostgreSQL, en acces local uniquement : 127.0.0.1:8010'
    Write-Output 'Les migrations ne sont pas appliquees automatiquement au demarrage.'
    Write-Output 'Arret : Ctrl+C. Le mot de passe reste en memoire seulement pendant ce processus.'
    & py $manage runserver 127.0.0.1:8010
    if ($LASTEXITCODE -ne 0) {
        throw ('Le serveur Django s est arrete avec le code ' + $LASTEXITCODE)
    }
} catch {
    Write-Error $_
    exit 1
} finally {
    foreach ($name in $environmentNames) {
        if ($null -eq $oldEnvironment[$name]) {
            Remove-Item -LiteralPath ('Env:' + $name) -ErrorAction SilentlyContinue
        } else {
            [System.Environment]::SetEnvironmentVariable($name, $oldEnvironment[$name], 'Process')
        }
    }
}
