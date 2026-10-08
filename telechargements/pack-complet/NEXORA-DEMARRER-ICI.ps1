param(
    [string]$Racine = ''
)

$ErrorActionPreference = 'Continue'
$origine = (Get-Location).Path
$horodatage = Get-Date -Format 'yyyyMMdd-HHmmss'
$bureau = [Environment]::GetFolderPath('Desktop')
if ([string]::IsNullOrWhiteSpace($bureau) -or -not (Test-Path -LiteralPath $bureau)) { $bureau = $env:USERPROFILE }

$pageSource = Join-Path $PSScriptRoot 'page.tsx'
$corrigeurBi = Join-Path $PSScriptRoot 'corriger_filtre_vendeur_bi.py'

try { Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null } catch { }

Write-Host '============================================================='
Write-Host ' NEXORA - PACK TOUT EN UN'
Write-Host '   1. Filtre vendeur du bilan BI (/reports) : installation'
Write-Host '   2. Sauvegarde COMPLETE de votre application (ZIP sur le Bureau)'
Write-Host '   3. Diagnostic cible pour le bilan vendeur du POS'
Write-Host '============================================================='
Write-Host ''

# --------------------------------------------------------------- outils ----
function Trouver-Programme($noms) {
    foreach ($n in $noms) {
        $c = Get-Command $n -ErrorAction SilentlyContinue
        if ($c) { return $n }
    }
    return ''
}

$python = Trouver-Programme @('py', 'python', 'python3')

function Est-Projet($d) {
    if (-not (Test-Path -LiteralPath (Join-Path $d 'manage.py'))) { return $false }
    if (-not (Test-Path -LiteralPath (Join-Path $d 'apps'))) { return $false }
    return $true
}

function Lire-Texte($chemin) {
    try { return [System.IO.File]::ReadAllText($chemin) } catch { return '' }
}

function Masquer-Secrets($texte) {
    $t = $texte
    $t = [System.Text.RegularExpressions.Regex]::Replace($t, "SECRET_KEY\s*=\s*['""][^'""]*['""]", "SECRET_KEY = '***MASQUE-PAR-LE-SCRIPT***'")
    $t = [System.Text.RegularExpressions.Regex]::Replace($t, "PASSWORD\s*[:=]\s*['""][^'""]*['""]", "PASSWORD: '***MASQUE-PAR-LE-SCRIPT***'")
    $t = [System.Text.RegularExpressions.Regex]::Replace($t, "postgres(ql)?://[^@\s'""]+@", "postgres://***MASQUE***@")
    return $t
}

# ------------------------------------------------ detection des projets ----
$candidats = @()
if ($Racine -ne '') { $candidats += $Racine }
$candidats += 'D:\NEXORA'
$candidats += 'C:\NEXORA'
$candidats += (Join-Path $env:USERPROFILE 'NEXORA')

$projets = @()
foreach ($c in $candidats) {
    if ([string]::IsNullOrWhiteSpace($c)) { continue }
    if (-not (Test-Path -LiteralPath $c)) { continue }
    if (-not (Est-Projet $c)) { continue }
    $complet = (Get-Item -LiteralPath $c).FullName
    if ($projets -notcontains $complet) { $projets += $complet }
}

if ($projets.Count -eq 0) {
    Write-Host '[ERREUR] Aucun projet NEXORA trouve.' -ForegroundColor Red
    Write-Host 'Un projet doit contenir manage.py ET le dossier apps.'
    Write-Host 'Cherche : D:\NEXORA, C:\NEXORA, %USERPROFILE%\NEXORA'
    Write-Host 'Relancez avec le bon dossier :'
    Write-Host '  powershell -ExecutionPolicy Bypass -File NEXORA-DEMARRER-ICI.ps1 -Racine D:\NEXORA'
    Write-Host ''
    Read-Host 'Appuyez sur Entree pour fermer'
    exit 1
}

Write-Host ('Projet(s) trouve(s) : ' + ($projets -join '   |   ')) -ForegroundColor Green
Write-Host ('Python : ' + $(if ($python -eq '') { 'INTROUVABLE' } else { $python }))
Write-Host ''

$exclus = @('node_modules', '.venv', 'venv', 'env', '.git', '__pycache__', '.next', '.turbo', 'dist', 'build',
            'coverage', '.mypy_cache', '.pytest_cache', 'media', 'staticfiles', '.idea', '.vscode',
            'sauvegardes-postgresql')

foreach ($projet in $projets) {
    Write-Host '-------------------------------------------------------------'
    Write-Host ('DOSSIER : ' + $projet) -ForegroundColor White

    $pageCible = Join-Path $projet 'frontend\src\app\reports\page.tsx'
    $biCible = Join-Path $projet 'apps\reports\bi_analytics.py'
    $suffixe = ((Split-Path $projet -Qualifier) + (Split-Path $projet -Leaf)) -replace '[:\\]', ''
    if ([string]::IsNullOrWhiteSpace($suffixe)) { $suffixe = 'projet' }

    # ------------------------------------------------ 1) filtre vendeur ----
    if ((Test-Path -LiteralPath $pageCible) -and (Test-Path -LiteralPath $pageSource)) {
        $sauve = Join-Path $projet ('sauvegardes-pack-tout-en-un-' + $horodatage)
        New-Item -ItemType Directory -Force -Path (Join-Path $sauve 'frontend\src\app\reports') | Out-Null
        Copy-Item -LiteralPath $pageCible -Destination (Join-Path $sauve 'frontend\src\app\reports\page.tsx') -Force
        if (Test-Path -LiteralPath $biCible) {
            New-Item -ItemType Directory -Force -Path (Join-Path $sauve 'apps\reports') | Out-Null
            Copy-Item -LiteralPath $biCible -Destination (Join-Path $sauve 'apps\reports\bi_analytics.py') -Force
        }

       $pageAvant = Get-Content -LiteralPath $pageCible -Raw
        $dejaBon = (($pageAvant -match 'selectedSeller') -and ($pageAvant -match 'seller_id=') -and ($pageAvant -match 'Tous les vendeurs'))
        if ($dejaBon) {
            Write-Host '  [1/3] Ecran /reports : filtre vendeur deja en place.' -ForegroundColor Green
        } else {
            Copy-Item -LiteralPath $pageSource -Destination $pageCible -Force
            $pageApres = Get-Content -LiteralPath $pageCible -Raw
            $ok = (($pageApres -match 'selectedSeller') -and ($pageApres -match 'seller_id=') -and ($pageApres -match 'Tous les vendeurs'))
            if ($ok) {
                Write-Host '  [1/3] Ecran /reports : filtre vendeur INSTALLE.' -ForegroundColor Green
            } else {
                Write-Host '  [1/3] Ecran /reports : ECHEC de la copie.' -ForegroundColor Red
                Copy-Item -LiteralPath (Join-Path $sauve 'frontend\src\app\reports\page.tsx') -Destination $pageCible -Force
                Write-Host '        Version precedente restauree automatiquement.' -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host '  [1/3] Ecran /reports : fichier introuvable, etape ignoree.' -ForegroundColor Yellow
    }

    if (Test-Path -LiteralPath $biCible) {
        $bi = Get-Content -LiteralPath $biCible -Raw
        if (($bi -match 'seller_id') -and ($bi -match 'available_sellers')) {
            Write-Host '  [1/3] Backend /reports : filtre seller_id deja present.' -ForegroundColor Green
        } else {
            Write-Host '  [1/3] Backend /reports : filtre absent, application...' -ForegroundColor Yellow
            if (($python -ne '') -and (Test-Path -LiteralPath $corrigeurBi)) {
                Set-Location -LiteralPath $projet
                & $python $corrigeurBi --racine $projet
            } else {
                Write-Host '        Python ou script correcteur indisponible.' -ForegroundColor Yellow
            }
        }
    }

    # ------------------------------------------- 2) sauvegarde complete ----
    $zipComplet = Join-Path $bureau ('NEXORA-sauvegarde-complete-' + $horodatage + '-' + $suffixe + '.zip')
    if (Test-Path -LiteralPath $zipComplet) { Remove-Item -LiteralPath $zipComplet -Force }
    $nombre = 0
    $octets = 0
    try {
        $archive = [System.IO.Compression.ZipFile]::Open($zipComplet, [System.IO.Compression.ZipArchiveMode]::Create)
        $pile = New-Object System.Collections.Stack
        $pile.Push($projet)
        while ($pile.Count -gt 0) {
            $dossier = $pile.Pop()
            $enfants = Get-ChildItem -LiteralPath $dossier -Force -ErrorAction SilentlyContinue
            foreach ($e in $enfants) {
                if ($e.PSIsContainer) {
                    if ($exclus -contains $e.Name.ToLower()) { continue }
                    $pile.Push($e.FullName)
                } else {
                    $nom = $e.Name.ToLower()
                    if ($nom.EndsWith('.pyc') -or $nom.EndsWith('.pyo') -or $nom.EndsWith('.dump')) { continue }
                    if ($e.Length -gt 104857600) { continue }
                    $rel = $e.FullName.Substring($projet.Length).TrimStart('\')
                    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $e.FullName, $rel, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
                    $nombre = $nombre + 1
                    $octets = $octets + $e.Length
                }
            }
        }
        $archive.Dispose()
        Write-Host ('  [2/3] Sauvegarde complete : ' + $zipComplet) -ForegroundColor Green
        Write-Host ('        ' + $nombre + ' fichiers, ' + [math]::Round($octets / 1MB, 1) + ' Mo avant compression')
    } catch {
        Write-Host ('  [2/3] Sauvegarde complete : ERREUR - ' + $_.Exception.Message) -ForegroundColor Red
    }

    # --------------------------------------------- 3) diagnostic POS ------
    $staging = Join-Path $env:TEMP ('nexora-diagnostic-' + $horodatage + '-' + $suffixe)
    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $staging | Out-Null

    $motsCles = @('seller', 'vendeur', 'sellers_performance', 'seller_id', 'bilan', 'cashier')
    $inclus = @()
    $pile = New-Object System.Collections.Stack
    $pile.Push($projet)
    while ($pile.Count -gt 0) {
        $dossier = $pile.Pop()
        $enfants = Get-ChildItem -LiteralPath $dossier -Force -ErrorAction SilentlyContinue
        foreach ($e in $enfants) {
            if ($e.PSIsContainer) {
                if ($exclus -contains $e.Name.ToLower()) { continue }
                $pile.Push($e.FullName)
                continue
            }
            $nom = $e.Name.ToLower()
            if ($nom.EndsWith('.pyc') -or $nom.EndsWith('.pyo') -or $nom.EndsWith('.map')) { continue }
            if ($e.Length -gt 400000) { continue }
            $rel = $e.FullName.Substring($projet.Length).TrimStart('\')
            $r = $rel.ToLower()
            if ($r.StartsWith('config\settings') -and -not ($nom.EndsWith('.py'))) { continue }
            $pertinent = $false
            if ($r.StartsWith('apps\pos\')) { $pertinent = $true }
            elseif ($r.StartsWith('apps\reports\')) { $pertinent = $true }
            elseif ($r.StartsWith('frontend\src\app\pos\')) { $pertinent = $true }
            elseif ($r.StartsWith('frontend\src\lib\')) { $pertinent = $true }
            elseif ($r -eq 'frontend\package.json') { $pertinent = $true }
            elseif ($r.StartsWith('config\settings') -and $nom.EndsWith('.py')) { $pertinent = $true }
            elseif ($nom.EndsWith('urls.py')) { $pertinent = $true }
            elseif (($r.StartsWith('apps\') -or $r.StartsWith('frontend\src\')) -and ($nom.EndsWith('.py') -or $nom.EndsWith('.tsx') -or $nom.EndsWith('.ts') -or $nom.EndsWith('.js'))) {
                $texte = (Lire-Texte $e.FullName).ToLower()
                foreach ($m in $motsCles) {
                    if ($texte.Contains($m)) { $pertinent = $true; break }
                }
            }
            if (-not $pertinent) { continue }
            if ($r.StartsWith('.env') -or $nom -eq '.env' -or $nom.StartsWith('.env.')) { continue }

            $destination = Join-Path $staging $rel
            New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
            if ($nom.EndsWith('.py') -or $nom.EndsWith('.tsx') -or $nom.EndsWith('.ts') -or $nom.EndsWith('.js') -or $nom.EndsWith('.json')) {
                $contenu = Lire-Texte $e.FullName
                if ($nom.EndsWith('settings.py')) { $contenu = Masquer-Secrets $contenu }
                [System.IO.File]::WriteAllText($destination, $contenu, [System.Text.Encoding]::UTF8)
            } else {
                Copy-Item -LiteralPath $e.FullName -Destination $destination -Force
            }
            $inclus += $rel
        }
    }

    if ($inclus.Count -eq 0) {
        Write-Host '  [3/3] Diagnostic : aucun fichier pertinent trouve.' -ForegroundColor Yellow
    } else {
        $manifeste = @()
        $manifeste += 'DIAGNOSTIC NEXORA - bilan de vente par vendeur (POS et rapports)'
        $manifeste += ('Projet : ' + $projet)
        $manifeste += ('Date   : ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
        $manifeste += 'Verification automatique : SECRET_KEY et mots de passe ont ete masques dans settings.py.'
        $manifeste += ''
        $manifeste += 'Fichiers inclus :'
        foreach ($i in ($inclus | Sort-Object)) { $manifeste += ('  - ' + $i) }
        [System.IO.File]::WriteAllText((Join-Path $staging 'LISTE-DES-FICHIERS.txt'), ($manifeste -join "`r`n"), [System.Text.Encoding]::UTF8)

        $zipDiag = Join-Path $env:TEMP ('nexora-diagnostic-' + $horodatage + '-' + $suffixe + '.zip')
        if (Test-Path -LiteralPath $zipDiag) { Remove-Item -LiteralPath $zipDiag -Force }
        try {
            [System.IO.Compression.ZipFile]::CreateFromDirectory($staging, $zipDiag)
            $b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($zipDiag))
            $tailleMorceau = 300000
            $fichiersEcrits = @()
            if ($b64.Length -le $tailleMorceau) {
                $cible = Join-Path $bureau ('nexora-diagnostic-pos-' + $horodatage + '-' + $suffixe + '.txt')
                [System.IO.File]::WriteAllText($cible, $b64, [System.Text.Encoding]::ASCII)
                $fichiersEcrits += $cible
            } else {
                $total = [math]::Ceiling($b64.Length / $tailleMorceau)
                for ($i = 0; $i -lt $total; $i++) {
                    $debut = $i * $tailleMorceau
                    $longueur = [math]::Min($tailleMorceau, $b64.Length - $debut)
                    $cible = Join-Path $bureau ('nexora-diagnostic-pos-' + $horodatage + '-' + $suffixe + '-partie' + ($i + 1) + '.txt')
                    [System.IO.File]::WriteAllText($cible, $b64.Substring($debut, $longueur), [System.Text.Encoding]::ASCII)
                    $fichiersEcrits += $cible
                }
            }
            Write-Host ('  [3/3] Diagnostic : ' + $inclus.Count + ' fichiers analyses.') -ForegroundColor Green
            foreach ($f in $fichiersEcrits) {
                Write-Host ('        A ENVOYER : ' + $f) -ForegroundColor Cyan
            }
        } catch {
            Write-Host ('  [3/3] Diagnostic : ERREUR - ' + $_.Exception.Message) -ForegroundColor Red
        }
    }

    if ($python -ne '') {
        Set-Location -LiteralPath $projet
        Write-Host '  Verification Django (manage.py check)...'
        & $python manage.py check
        Set-Location -LiteralPath $origine
    }
    Write-Host ''
}

Set-Location -LiteralPath $origine

Write-Host '============================================================='
Write-Host ' TERMINE' -ForegroundColor Cyan
Write-Host '============================================================='
Write-Host ''
Write-Host 'SUR VOTRE BUREAU :'
Write-Host '  - NEXORA-sauvegarde-complete-<date>.zip : votre application entiere'
Write-Host '    (sans node_modules, sans environnements virtuels, sans archives).'
Write-Host '    Utilisez ce fichier comme sauvegarde de reference.'
Write-Host '  - nexora-diagnostic-pos-<date>.txt (ou -partie1, -partie2...) :'
Write-Host '    a ATTACHER dans la conversation pour que je corrige le bilan de'
Write-Host '    vente par vendeur au niveau du POS.'
Write-Host ''
Write-Host 'POUR RELANCER L APPLICATION :'
Write-Host '  1. Backend, dans le dossier du projet affiche ci-dessus :'
Write-Host '       py manage.py runserver'
Write-Host '  2. Frontend, dans le sous-dossier frontend :'
Write-Host '       cd frontend'
Write-Host '       npm run dev'
Write-Host ''
Read-Host 'Appuyez sur Entree pour fermer'
