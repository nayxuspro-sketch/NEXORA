param(
    [string]$Racine = ''
)

$ErrorActionPreference = 'Stop'
$origine     = (Get-Location).Path
$pageSource  = Join-Path $PSScriptRoot 'page.tsx'
$horodatage  = Get-Date -Format 'yyyyMMdd-HHmmss'

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' NEXORA - SOLUTION FINALE : filtre de vente par vendeur' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''

if (-not (Test-Path -LiteralPath $pageSource)) {
    Write-Host '[ERREUR] page.tsx est introuvable a cote de ce script.' -ForegroundColor Red
    Read-Host 'Appuyez sur Entree pour fermer'; exit 1
}

# ------------------------------------------------------------------ outils --
function Resoudre-Python {
    foreach ($candidat in @('py', 'python')) {
        $commande = Get-Command $candidat -ErrorAction SilentlyContinue
        if ($commande) { return $candidat }
    }
    return ''
}

function Tester-Projet([string]$dossier) {
    if (-not (Test-Path -LiteralPath (Join-Path $dossier 'manage.py'))) { return $false }
    if (-not (Test-Path -LiteralPath (Join-Path $dossier 'frontend\src\app\reports\page.tsx'))) { return $false }
    return $true
}

# ------------------------------------------- recherche des copies du projet --
$candidats = @()
if ($Racine -ne '') { $candidats += $Racine }
$candidats += 'D:\NEXORA', 'C:\NEXORA', (Join-Path $env:USERPROFILE 'NEXORA')

$projets = @()
foreach ($candidat in $candidats) {
    if ([string]::IsNullOrWhiteSpace($candidat)) { continue }
    if (-not (Test-Path -LiteralPath $candidat)) { continue }
    if (-not (Tester-Projet $candidat)) { continue }
    $complet = (Get-Item -LiteralPath $candidat).FullName
    $existe = $false
    foreach ($p in $projets) { if ($p -eq $complet) { $existe = $true } }
    if (-not $existe) { $projets += $complet }
}

if ($projets.Count -eq 0) {
    Write-Host '[ERREUR] Aucun projet NEXORA complet trouve.' -ForegroundColor Red
    Write-Host 'Cherche un dossier contenant manage.py ET frontend\src\app\reports\page.tsx.'
    Write-Host 'Relancez en indiquant le bon dossier, par exemple :'
    Write-Host '  powershell -ExecutionPolicy Bypass -File INSTALLER-SOLUTION-FINALE.ps1 -Racine D:\NEXORA'
    Write-Host ''
    Read-Host 'Appuyez sur Entree pour fermer'; exit 1
}

Write-Host ('Projet(s) detecte(s) : ' + ($projets -join '  |  ')) -ForegroundColor Green
Write-Host ''

$python = Resoudre-Python
$echecs = @()

foreach ($projet in $projets) {
    Write-Host ('------------------------------------------------------------') -ForegroundColor DarkGray
    Write-Host ('Dossier traite : ' + $projet) -ForegroundColor White
    $pageCible = Join-Path $projet 'frontend\src\app\reports\page.tsx'
    $biCible   = Join-Path $projet 'apps\reports\bi_analytics.py'
    $dossierSauve = Join-Path $projet ("sauvegardes-solution-finale-" + $horodatage)

    # 1) sauvegarde
    New-Item -ItemType Directory -Force -Path (Join-Path $dossierSauve 'frontend\src\app\reports') | Out-Null
    Copy-Item -LiteralPath $pageCible -Destination (Join-Path $dossierSauve 'frontend\src\app\reports\page.tsx') -Force
    if (Test-Path -LiteralPath $biCible) {
        New-Item -ItemType Directory -Force -Path (Join-Path $dossierSauve 'apps\reports') | Out-Null
        Copy-Item -LiteralPath $biCible -Destination (Join-Path $dossierSauve 'apps\reports\bi_analytics.py') -Force
    }
    Write-Host ('  Sauvegarde : ' + $dossierSauve) -ForegroundColor Green

    # 2) installation de l ecran final complet
    Copy-Item -LiteralPath $pageSource -Destination $pageCible -Force
    $page = Get-Content -LiteralPath $pageCible -Raw
    $manquants = @()
    if ($page -notmatch 'selectedSeller')    { $manquants += 'etat React' }
    if ($page -notmatch 'seller_id=')        { $manquants += 'envoi de seller_id' }
    if ($page -notmatch 'Tous les vendeurs') { $manquants += 'liste deroulante' }
    if ($manquants.Count -gt 0) {
        Write-Host ('  [ERREUR] copie incomplete : ' + ($manquants -join ', ')) -ForegroundColor Red
        $echecs += $projet
        continue
    }
    Write-Host '  Ecran /reports : liste deroulante des vendeurs installee.' -ForegroundColor Green

    # 3) backend : corrige uniquement s il manque le filtre
    if (Test-Path -LiteralPath $biCible) {
        $bi = Get-Content -LiteralPath $biCible -Raw
        if (($bi -match 'seller_id') -and ($bi -match 'available_sellers')) {
            Write-Host '  Backend : filtre seller_id deja present.' -ForegroundColor Green
        } else {
            Write-Host '  Backend : filtre absent, application du correctif...' -ForegroundColor Yellow
            $scriptBi = Join-Path $PSScriptRoot 'corriger_filtre_vendeur_bi.py'
            if (($python -ne '') -and (Test-Path -LiteralPath $scriptBi)) {
                Set-Location -LiteralPath $projet
                & $python $scriptBi --racine $projet
                if ($LASTEXITCODE -ne 0) {
                    Write-Host '  [ATTENTION] correctif backend incomplet : collez la sortie ci-dessus.' -ForegroundColor Yellow
                    $echecs += $projet
                } else {
                    Write-Host '  Backend : corrige.' -ForegroundColor Green
                }
            } else {
                Write-Host '  [ATTENTION] Python ou corriger_filtre_vendeur_bi.py indisponible : backend non corrige.' -ForegroundColor Yellow
                $echecs += $projet
            }
        }
    } else {
        Write-Host '  [ATTENTION] apps\reports\bi_analytics.py introuvable : backend non verifie.' -ForegroundColor Yellow
        $echecs += $projet
    }

    # 4) verification Django
    if ($python -ne '') {
        Set-Location -LiteralPath $projet
        & $python manage.py check
        if ($LASTEXITCODE -ne 0) {
            Write-Host '  [ATTENTION] manage.py check a signale une erreur.' -ForegroundColor Yellow
            $echecs += $projet
        } else {
            Write-Host '  manage.py check : aucune erreur.' -ForegroundColor Green
        }
    } else {
        Write-Host '  [ATTENTION] Python introuvable : manage.py check non lance.' -ForegroundColor Yellow
    }
    Write-Host ''
}

Set-Location -LiteralPath $origine

Write-Host '============================================================' -ForegroundColor Cyan
if ($echecs.Count -eq 0) {
    Write-Host ' TERMINE SUR TOUS LES DOSSIERS DETECTES' -ForegroundColor Cyan
} else {
    Write-Host (' TERMINE AVEC AVERTISSEMENTS : ' + ($echecs -join ', ')) -ForegroundColor Yellow
}
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'REDEMARRAGE (a faire dans l ordre) :' -ForegroundColor White
Write-Host '  1. Backend, depuis le dossier DU PROJET :'
Write-Host '       cd <dossier indique ci-dessus>'
Write-Host '       py manage.py runserver'
Write-Host '     Si Windows refuse le port 8000, Windows affiche :'
Write-Host '       "You don''t have permission to access that port"'
Write-Host '     Voir la section dediee du LISEZMOI.'
Write-Host '  2. Frontend, dans le sous-dossier frontend (c est la qu est package.json) :'
Write-Host '       cd <dossier>\frontend'
Write-Host '       npm run dev'
Write-Host '  3. Ouvrez /reports : la liste deroulante "Tous les vendeurs" est a cote'
Write-Host '     des boutons 7 jours / 30 jours / Trimestre.'
Write-Host ''
Read-Host 'Appuyez sur Entree pour fermer'
