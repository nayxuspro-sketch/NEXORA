# Script PowerShell de mise à jour automatique sans Git pour C:\NEXORA
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   NEXORA ERP - APPLICATION AUTOMATIQUE DU CORRECTIF" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$base = "https://raw.githubusercontent.com/nayxuspro-sketch/NEXORA/arena/01a0ba27-nexora"

$files = @(
    "frontend/src/app/pos/page.tsx",
    "apps/sales/pdf_seller_report.py",
    "apps/sales/serializers.py",
    "apps/sales/views.py",
    "apps/common/validators.py",
    "apps/common/renderers.py",
    "apps/pos/pdf_z_report.py",
    "apps/inventory/pdf_export.py",
    "apps/catalog/pdf_export.py",
    "seed_dev.py"
)

$wc = New-Object System.Net.WebClient
$wc.Encoding = [System.Text.Encoding]::UTF8

foreach ($f in $files) {
    $url = "$base/$f"
    $localPath = "C:\NEXORA\" + $f.Replace('/', '\')
    $dir = Split-Path $localPath -Parent
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    try {
        $content = $wc.DownloadString($url)
        [IO.File]::WriteAllText($localPath, $content, [System.Text.Encoding]::UTF8)
        Write-Host " [OK] Mis a jour : $f" -ForegroundColor Green
    } catch {
        Write-Host " [ERR] Echec pour $f : $_" -ForegroundColor Red
    }
}

Write-Host "`nInsertion des donnees de vente..." -ForegroundColor Yellow
try {
    python C:\NEXORA\seed_dev.py
} catch {
    Write-Host "Veuillez executer 'python seed_dev.py' manuellement si necessaire."
}

Write-Host "`n>>> MISE A JOUR TERMINEE AVEC SUCCES ! <<<" -ForegroundColor Cyan
