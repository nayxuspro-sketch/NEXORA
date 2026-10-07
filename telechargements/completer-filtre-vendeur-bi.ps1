$ErrorActionPreference = 'Stop'
$projectRoot = 'D:\NEXORA'
$patchScript = Join-Path $PSScriptRoot 'completer_filtre_vendeur_bi.py'

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'manage.py'))) {
    Write-Host '[ERREUR] manage.py est introuvable dans D:\NEXORA.' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $patchScript)) {
    Write-Host '[ERREUR] completer_filtre_vendeur_bi.py doit rester a cote de ce script.' -ForegroundColor Red
    exit 1
}

Set-Location -LiteralPath $projectRoot
Write-Host 'Complement du filtre vendeur de l ecran Business Intelligence (/reports).' -ForegroundColor Cyan
Write-Host 'Ajoute ce qui manque dans frontend\src\app\reports\page.tsx :'
Write-Host '  liste deroulante des vendeurs, envoi de seller_id, libelle du perimetre, export PDF.'
Write-Host 'Sauvegarde horodatee avant modification. Aucun autre fichier touche.'
Write-Host ''

& py $patchScript --racine $projectRoot
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host '[ARRET] Element critique non insere : rien n a ete ecrit.' -ForegroundColor Yellow
    Write-Host 'Collez dans la conversation les reperes de lignes affiches ci-dessus.' -ForegroundColor Yellow
    exit $code
}

Write-Host ''
Write-Host '[OK] Ecran BI complete.' -ForegroundColor Green
Write-Host 'Ensuite :' -ForegroundColor Cyan
Write-Host '  1. Relancez le frontend (npm run dev) puis rechargez /reports.'
Write-Host '  2. La liste deroulante doit proposer "Tous les vendeurs" et chaque vendeur.'
Write-Host '  3. En choisissant un vendeur, les KPI, produits, familles, magasins et marges'
Write-Host '     doivent se recalculer sur ce vendeur uniquement.'
Write-Host ''
Write-Host 'Optionnel, tests backend :' -ForegroundColor Cyan
Write-Host '  py manage.py test tests.test_bi_vendeur_filtre -v 2'
