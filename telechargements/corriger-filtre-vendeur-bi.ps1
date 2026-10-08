$ErrorActionPreference = 'Stop'
$projectRoot = 'D:\NEXORA'
$patchScript = Join-Path $PSScriptRoot 'corriger_filtre_vendeur_bi.py'
$modelePage = Join-Path $PSScriptRoot 'page-bi-filtre-vendeur.tsx'

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'manage.py'))) {
    Write-Host '[ERREUR] manage.py est introuvable dans D:\NEXORA.' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $patchScript)) {
    Write-Host '[ERREUR] corriger_filtre_vendeur_bi.py doit rester a cote de ce script.' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $modelePage)) {
    Write-Host '[ERREUR] page-bi-filtre-vendeur.tsx doit rester a cote de ce script.' -ForegroundColor Red
    exit 1
}

Set-Location -LiteralPath $projectRoot
Write-Host 'Correctif du filtre vendeur de l ecran Business Intelligence (/reports).' -ForegroundColor Cyan
Write-Host '  1. apps\reports\bi_analytics.py  -> parametre seller_id + available_sellers'
Write-Host '  2. frontend\src\app\reports\page.tsx -> liste deroulante des vendeurs'
Write-Host 'Une sauvegarde horodatee des deux fichiers est creee avant toute modification.'
Write-Host ''

& py $patchScript --racine $projectRoot
$patchExitCode = $LASTEXITCODE
if ($patchExitCode -ne 0) {
    Write-Host '[ARRET] Le correctif n a pas ete applique. Aucune modification partielle.' -ForegroundColor Yellow
    exit $patchExitCode
}

Write-Host ''
Write-Host 'Verification Django (manage.py check), sans migration...' -ForegroundColor Cyan
& py manage.py check
$checkExitCode = $LASTEXITCODE
if ($checkExitCode -ne 0) {
    Write-Host '[ATTENTION] manage.py check a signale une erreur. Restaurez la sauvegarde indiquee ci-dessus.' -ForegroundColor Yellow
    exit $checkExitCode
}
Write-Host '[OK] manage.py check reussi.' -ForegroundColor Green

$reponse = Read-Host 'Lancer aussi les tests automatiques (base de test) ? O/N'
if ($reponse -eq 'O' -or $reponse -eq 'o') {
    Write-Host 'Tests du filtre vendeur...' -ForegroundColor Cyan
    & py manage.py test tests.test_bi_vendeur_filtre -v 2
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[ATTENTION] Les tests ont signale un probleme : collez la sortie complete.' -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host 'Termine. Collez la sortie complete de cette fenetre dans la conversation.' -ForegroundColor Green
Write-Host 'Puis : redemarrez Django, et cote frontend relancez npm run dev.' -ForegroundColor Green
