$ErrorActionPreference = 'Stop'
$projectRoot = 'D:\NEXORA'
$patchScript = Join-Path $PSScriptRoot 'corriger_bilan_vendeur.py'

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'manage.py'))) {
    Write-Host '[ERREUR] manage.py est introuvable dans D:\NEXORA.' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $patchScript)) {
    Write-Host '[ERREUR] corriger_bilan_vendeur.py doit rester a cote du script PowerShell.' -ForegroundColor Red
    exit 1
}

Set-Location -LiteralPath $projectRoot
Write-Host 'Correction ciblee du bilan vendeur dans apps\reports\views.py.' -ForegroundColor Cyan
Write-Host 'Le script sauvegarde le fichier, puis limite le role CASHIER a ses ventes.'
Write-Host 'Aucune migration ni ecriture dans PostgreSQL.'

& py $patchScript $projectRoot
$patchExitCode = $LASTEXITCODE
if ($patchExitCode -ne 0) {
    Write-Host '[ARRET] Le patch n a pas ete applique ou les validations ont echoue.' -ForegroundColor Yellow
    exit $patchExitCode
}

Write-Host ''
Write-Host 'Verification Django (manage.py check), sans migration...' -ForegroundColor Cyan
& py manage.py check
$checkExitCode = $LASTEXITCODE
if ($checkExitCode -ne 0) {
    Write-Host '[ATTENTION] manage.py check a signale une erreur. Le fichier sauvegarde est indique ci-dessus.' -ForegroundColor Yellow
    exit $checkExitCode
}
Write-Host '[OK] Verification Django reussie.' -ForegroundColor Green
