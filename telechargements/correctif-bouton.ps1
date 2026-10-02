# ============================================================
# Correctif de disposition du bouton « Ouvrir dans un onglet (Direct) »
# Fenêtre « Exporter le Catalogue des Produits en PDF (par Statut) »
#
# Ce script :
#   1. cherche le template Django contenant </body> (base) ou, à défaut,
#      celui contenant le bouton « Ouvrir dans un onglet » ;
#   2. en fait une sauvegarde (.sauvegarde-avant-correctif) ;
#   3. y injecte un correctif JavaScript universel (ASCII uniquement) :
#      - le libellé du bouton reste sur UNE seule ligne (white-space: nowrap) ;
#      - le bouton ne se fait plus compresser (flex: 0 0 auto, width/height auto) ;
#      - le conteneur du bouton passe en flex propre (gap, wrap, centrage)
#        uniquement s'il ne contient que des boutons/liens ;
#      - un MutationObserver corrige aussi les modales ouvertes plus tard ;
#   4. est idempotent : relancé, il ne modifie rien de plus.
#
# Annulation : restaurer le fichier .sauvegarde-avant-correctif
# ============================================================

$Projet = "C:\NEXORA"     # <- seule ligne a adapter si votre projet est ailleurs

$marqueur = "correctif-disposition-bouton"

$js = @'
<script>
/* correctif-disposition-bouton : garde le libelle sur une ligne et empeche */
/* l'ecrasement du bouton, quel que soit le CSS d'origine. ASCII uniquement. */
(function () {
  function corriger(btn) {
    if (btn.getAttribute("data-fr-fix")) return;
    btn.setAttribute("data-fr-fix", "1");
    btn.style.whiteSpace = "nowrap";
    btn.style.flex = "0 0 auto";
    btn.style.width = "auto";
    btn.style.height = "auto";
    btn.style.alignSelf = "center";
    var p = btn.parentElement;
    if (!p) return;
    var ok = p.children.length > 0;
    for (var i = 0; i < p.children.length; i++) {
      var t = p.children[i].tagName;
      if (t !== "BUTTON" && t !== "A") { ok = false; break; }
    }
    if (ok) {
      p.style.display = "flex";
      p.style.alignItems = "center";
      p.style.gap = "10px";
      p.style.flexWrap = "wrap";
    }
  }
  function scanner(racine) {
    var zone = racine || document;
    var btns = zone.querySelectorAll("button, a");
    for (var i = 0; i < btns.length; i++) {
      if (/Ouvrir dans un onglet/i.test(btns[i].textContent)) corriger(btns[i]);
    }
  }
  function demarrer() {
    scanner();
    if (typeof MutationObserver === "undefined") return;
    new MutationObserver(function (muts) {
      for (var i = 0; i < muts.length; i++) {
        var nodes = muts[i].addedNodes;
        for (var j = 0; j < nodes.length; j++) {
          if (nodes[j].nodeType === 1) scanner(nodes[j]);
        }
      }
      scanner();
    }).observe(document.body, { childList: true, subtree: true });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", demarrer);
  } else { demarrer(); }
})();
</script>
'@

# ---- 1. Recenser les templates (en excluant venv, node_modules, .git) ----
$fichiers = Get-ChildItem -Path $Projet -Recurse -Include *.html -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "\\(venv|env|node_modules|\.git|staticfiles)\\" }

$cible = $null
$mode  = ""
foreach ($f in $fichiers) {
    if (([System.IO.File]::ReadAllText($f.FullName)) -match "</body>") { $cible = $f; $mode = "base"; break }
}
if (-not $cible) {
    foreach ($f in $fichiers) {
        if (([System.IO.File]::ReadAllText($f.FullName)) -match "Ouvrir dans un onglet") { $cible = $f; $mode = "modale"; break }
    }
}

if (-not $cible) {
    Write-Host "Aucun template trouvant contenant </body> ou le bouton : collez le correctif a la main." -ForegroundColor Red
    Write-Host $js
    break
}

# ---- 2. Idempotence + sauvegarde ----
$txt = [System.IO.File]::ReadAllText($cible.FullName)
if ($txt.Contains($marqueur)) {
    Write-Host "Deja corrige : $($cible.FullName) (rien a faire)." -ForegroundColor Yellow
    break
}
Copy-Item $cible.FullName "$($cible.FullName).sauvegarde-avant-correctif" -Force
Write-Host "Sauvegarde : $($cible.FullName).sauvegarde-avant-correctif" -ForegroundColor DarkGray

# ---- 3. Injection ----
$utf8 = New-Object System.Text.UTF8Encoding $false
if ($mode -eq "base") {
    $nouveau = $txt.Replace("</body>", $js + "`r`n</body>")
} else {
    $lignes = [System.IO.File]::ReadAllLines($cible.FullName)
    $sortie = New-Object System.Collections.Generic.List[string]
    foreach ($l in $lignes) {
        $sortie.Add($l)
        if ($l -match "Ouvrir dans un onglet") { $sortie.Add($js) }
    }
    $nouveau = $sortie -join "`r`n"
}
[System.IO.File]::WriteAllText($cible.FullName, $nouveau, $utf8)

Write-Host ""
Write-Host "Correctif injecte dans : $($cible.FullName) (mode : $mode)" -ForegroundColor Green
Write-Host "Etapes suivantes :" -ForegroundColor Cyan
Write-Host "  1. Redemarrez le serveur (py manage.py runserver ...) ou rechargez la page avec Ctrl+F5."
Write-Host "  2. Ouvrez la fenetre d'export PDF : le bouton reste sur une seule ligne."
Write-Host "  3. Pour annuler : restaurez $($cible.FullName).sauvegarde-avant-correctif"
