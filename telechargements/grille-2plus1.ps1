# ============================================================
# grille-2plus1.ps1
# Applique la disposition « 2 + 1 » (Annuler | Ouvrir sur une rangée,
# action primaire pleine largeur dessous) a TOUS les pieds de modales
# d'export contenant le lien « Ouvrir dans un onglet », dans tous les
# fichiers .tsx du front Next.js.
#
# - Sauvegarde automatique : <fichier>.sauvegarde-grille
# - Idempotent : les pieds deja en grille sont ignores
# - N'approche que les pieds contenant le lien d'export (les autres
#   modales ne sont pas touchees)
# - Si un fichier contient le lien mais n'est PAS modifie, affiche le
#   contexte reel autour du bouton (pour diagnostic)
# ============================================================

$Projet = "C:\NEXORA"     # <- a adapter si besoin
$utf8 = New-Object System.Text.UTF8Encoding $false
$total = 0

foreach ($f in (Get-ChildItem "$Projet\frontend\src" -Recurse -Include *.tsx -File -ErrorAction SilentlyContinue)) {
    $lignes = [System.IO.File]::ReadAllLines($f.FullName)
    $modifie = $false; $dansPied = $false; $restant = 0

    for ($i = 0; $i -lt $lignes.Count; $i++) {
        $l = $lignes[$i]
        if (-not $dansPied -and $l -match 'flex-col-reverse sm:flex-row flex-wrap justify-end gap-2') {
            $lignes[$i] = $l.Replace('flex flex-col-reverse sm:flex-row flex-wrap justify-end gap-2', 'grid grid-cols-1 sm:grid-cols-2 gap-2')
            $dansPied = $true; $restant = 40; $modifie = $true; continue
        }
        if ($dansPied) {
            if     ($l -match 'className="w-full sm:w-auto font-medium"')    { $lignes[$i] = $l.Replace('className="w-full sm:w-auto font-medium"', 'className="w-full font-medium"'); $modifie = $true }
            elseif ($l -match 'w-full sm:w-auto whitespace-nowrap shrink-0') { $lignes[$i] = $l.Replace('w-full sm:w-auto whitespace-nowrap shrink-0', 'w-full whitespace-nowrap'); $modifie = $true }
            elseif ($l -match 'className="w-full sm:w-auto"')                { $lignes[$i] = $l.Replace('className="w-full sm:w-auto"', 'className="w-full -order-1 sm:order-none sm:col-span-2"'); $modifie = $true }
            $restant--
            if ($restant -le 0 -or $l -match '</Modal>') { $dansPied = $false }
        }
    }

    if ($modifie) {
        if (-not (Test-Path "$($f.FullName).sauvegarde-grille")) { Copy-Item $f.FullName "$($f.FullName).sauvegarde-grille" -Force }
        [System.IO.File]::WriteAllLines($f.FullName, $lignes, $utf8)
        $total++
        Write-Host "grille 2+1 : $($f.FullName)" -ForegroundColor Green
    }
    elseif (([System.IO.File]::ReadAllText($f.FullName)) -match "Ouvrir dans un onglet") {
        Write-Host "NON MODIFIE (motif absent) : $($f.FullName) — contexte autour du bouton :" -ForegroundColor Yellow
        for ($i = 0; $i -lt $lignes.Count; $i++) {
            if ($lignes[$i] -match 'Ouvrir dans un onglet') {
                $debut = [Math]::Max(0, $i - 10); $fin = [Math]::Min($lignes.Count - 1, $i + 4)
                for ($j = $debut; $j -le $fin; $j++) { Write-Host ("  {0}: {1}" -f ($j + 1), $lignes[$j]) }
                Write-Host "  ---"
            }
        }
    }
}

if ($total -eq 0) {
    Write-Host "Aucun pied de modale modifie : collez-moi les contextes affiches ci-dessus." -ForegroundColor Yellow
} else {
    Write-Host "$total fichier(s) mis a jour. Le dev Next recompile a chaud : Ctrl+F5 cote navigateur." -ForegroundColor Cyan
}
