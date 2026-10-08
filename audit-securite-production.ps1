# Audit de configuration Django avant production (lecture seule).
# Le script n'affiche aucun mot de passe, SECRET_KEY, hote autorise ni origine CORS.
# Il ne modifie ni le code, ni la base, ni les migrations.

$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$manage = Join-Path $project 'manage.py'
$pythonAudit = Join-Path $project 'audit_configuration_production.py'
$serviceName = 'postgresql-x64-18'
$environmentNames = @('DB_ENGINE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DJANGO_SETTINGS_MODULE')
$oldEnvironment = @{}
foreach ($name in $environmentNames) {
    $oldEnvironment[$name] = [System.Environment]::GetEnvironmentVariable($name, 'Process')
}
$exitCode = 0

try {
    if (-not (Test-Path -LiteralPath $manage)) {
        throw ('manage.py introuvable dans ' + $project + '. Extrayez les fichiers dans D:\NEXORA.')
    }
    if (-not (Test-Path -LiteralPath $pythonAudit)) {
        throw 'audit_configuration_production.py est manquant.'
    }
    if (-not (Get-Command 'py' -ErrorAction SilentlyContinue)) {
        throw 'Le lanceur Python py est introuvable.'
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
    $env:DJANGO_SETTINGS_MODULE = 'config.settings'

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

    Write-Output '============================================================'
    Write-Output 'AUDIT PRE-PRODUCTION NEXORA (LECTURE SEULE)'
    Write-Output 'Les secrets, hotes et origines internes ne sont pas affiches.'
    Write-Output 'Aucune migration ni ecriture dans la base ne sera lancee.'
    Write-Output '============================================================'
    Write-Output ''
    Write-Output '=== 1. Configuration Django effective et connexion PostgreSQL ==='
    & py $pythonAudit
    if ($LASTEXITCODE -ne 0) {
        throw ('Le diagnostic Django a echoue avec le code ' + $LASTEXITCODE + '.')
    }

    Write-Output ''
    Write-Output '=== 2. Controles Django pour le deploiement (manage.py check --deploy) ==='
    & py $manage check --deploy
    $checkExitCode = $LASTEXITCODE
    if ($checkExitCode -ne 0) {
        Write-Output ('CHECK_DEPLOY_EXIT=' + $checkExitCode)
        $exitCode = 1
    } else {
        Write-Output 'CHECK_DEPLOY_EXIT=0'
        Write-Output 'Le code 0 peut coexister avec des avertissements : examinez toutes les lignes ci-dessus.'
    }

    Write-Output ''
    Write-Output 'Audit termine. Ne partagez jamais un mot de passe ou une SECRET_KEY.'
} catch {
    Write-Output ('ECHEC : ' + $_.Exception.Message)
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
