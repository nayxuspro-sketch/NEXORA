$ErrorActionPreference = 'Stop'

$projectRoot  = 'D:\NEXORA'
$pageCible    = Join-Path $projectRoot 'frontend\src\app\reports\page.tsx'
$pageSource   = Join-Path $PSScriptRoot 'page.tsx'
$biCible      = Join-Path $projectRoot 'apps\reports\bi_analytics.py'
$horodatage   = Get-Date -Format 'yyyyMMdd-HHmmss'
$dossierSauve = Join-Path $projectRoot ("sauvegardes-solution-finale-" + $horodatage)

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' NEXORA - SOLUTION FINALE : filtre de vente par vendeur' -ForegroundColor Cyan
Write-Host ' (ecran Business Intelligence & Decision)' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''

# --- 1) Verifications prealables ------------------------------------------
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'manage.py'))) {
    Write-Host '[ERREUR] manage.py est introuvable dans D:\NEXORA.' -ForegroundColor Red
    Write-Host 'Modifiez $projectRoot en tete de ce script si votre projet est ailleurs.'
    Read-Host 'Appuyez sur Entree pour fermer'
    exit 1
}
if (-not (Test-Path -LiteralPath $pageSource)) {
    Write-Host '[ERREUR] page.tsx est introuvable a cote de ce script.' -ForegroundColor Red
    Read-Host 'Appuyez sur Entree pour fermer'
    exit 1
}
if (-not (Test-Path -LiteralPath (Split-Path $pageCible))) {
    Write-Host ('[ERREUR] Dossier introuvable : ' + (Split-Path $pageCible)) -ForegroundColor Red
    Read-Host 'Appuyez sur Entree pour fermer'
    exit 1
}

# --- 2) Sauvegarde de la version actuelle --------------------------------
New-Item -ItemType Directory -Force -Path (Split-Path (Join-Path $dossierSauve 'frontend\src\app\reports\page.tsx')) | Out-Null
Copy-Item -LiteralPath $pageCible -Destination (Join-Path $dossierSauve 'frontend\src\app\reports\page.tsx') -Force
if (Test-Path -LiteralPath $biCible) {
    New-Item -ItemType Directory -Force -Path (Join-Path $dossierSauve 'apps\reports') | Out-Null
    Copy-Item -LiteralPath $biCible -Destination (Join-Path $dossierSauve 'apps\reports\bi_analytics.py') -Force
}
Write-Host ('[1/4] Sauvegarde complete : ' + $dossierSauve) -ForegroundColor Green
Write-Host '      (vos anciennes versions y sont conservees telles quelles)'

# --- 3) Remplacement de l ecran par la version finale --------------------
Copy-Item -LiteralPath $pageSource -Destination $pageCible -Force
$page = Get-Content -LiteralPath $pageCible -Raw
$manquants = @()
if ($page -notmatch 'selectedSeller')      { $manquants += 'etat React' }
if ($page -notmatch 'seller_id=')          { $manquants += 'envoi de seller_id' }
if ($page -notmatch 'Tous les vendeurs')   { $manquants += 'liste deroulante' }
if ($manquants.Count -gt 0) {
    Write-Host ('[ERREUR] Copie incomplete : ' + ($manquants -join ', ')) -ForegroundColor Red
    Read-Host 'Appuyez sur Entree pour fermer'
    exit 1
}
Write-Host '[2/4] Ecran /reports mis a jour : liste deroulante des vendeurs installee.' -ForegroundColor Green

# --- 4) Verification du backend (aucune modification) --------------------
$bi = Get-Content -LiteralPath $biCible -Raw
if (($bi -match 'seller_id') -and ($bi -match 'available_sellers')) {
    Write-Host '[3/4] Backend deja correct : filtre seller_id et liste des vendeurs presents.' -ForegroundColor Green
} else {
    Write-Host '[3/4] Le backend ne contient pas encore le filtre : application du correctif...' -ForegroundColor Yellow
    $scriptBi = Join-Path $PSScriptRoot 'corriger_filtre_vendeur_bi.py'
    if (Test-Path -LiteralPath $scriptBi) {
        & py $scriptBi --racine $projectRoot
        if ($LASTEXITCODE -ne 0) {
            Write-Host '[ATTENTION] Le backend doit etre corrige manuellement : collez la sortie ci-dessus.' -ForegroundColor Yellow
        } else {
            Write-Host '      Backend corrige.' -ForegroundColor Green
        }
    } else {
        Write-Host '[ATTENTION] corriger_filtre_vendeur_bi.py absent : backend non corrige.' -ForegroundColor Yellow
    }
}

# --- 5) Verification globale Django --------------------------------------
Set-Location -LiteralPath $projectRoot
Write-Host '[4/4] Verification Django (manage.py check)...'
& py manage.py check
if ($LASTEXITCODE -ne 0) {
    Write-Host '[ATTENTION] manage.py check a signale une erreur : collez la sortie ci-dessus.' -ForegroundColor Yellow
} else {
    Write-Host '      manage.py check : aucune erreur.' -ForegroundColor Green
}

Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' TERMINE - il ne reste qu a redemarrer pour voir le filtre' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host '1. Backend Django : Ctrl+C dans sa fenetre, puis :' -ForegroundColor White
Write-Host '     py manage.py runserver'
Write-Host '2. Frontend : Ctrl+C dans sa fenetre, puis :' -ForegroundColor White
Write-Host '     npm run dev'
Write-Host '3. Ouvrez l ecran Business Intelligence (/reports) :' -ForegroundColor White
Write-Host '     la liste deroulante "Tous les vendeurs" est a cote des'
Write-Host '     boutons 7 jours / 30 jours / Trimestre.'
Write-Host '     Choisissez un vendeur : CA, marge, panier moyen, produits,'
Write-Host '     familles, magasins et ventes se recalculent sur ce vendeur.'
Write-Host ''
Write-Host 'Retour arriere eventuel : recopiez page.tsx depuis' -ForegroundColor DarkGray
Write-Host ('  ' + $dossierSauve) -ForegroundColor DarkGray
Write-Host ''
Read-Host 'Appuyez sur Entree pour fermer'
