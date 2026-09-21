import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs('/home/user/NEXORA/docs/screenshots', exist_ok=True)
os.makedirs('/home/user/NEXORA/frontend/public/docs/screenshots', exist_ok=True)

def draw_topbar(draw, width, title="NEXORA ENTERPRISE ERP & POS"):
    draw.rectangle([0, 0, width, 55], fill='#0f172a')
    draw.rectangle([20, 12, 110, 42], fill='#0284c7')
    draw.text((32, 20), "NEXORA", fill='#ffffff')
    draw.text((130, 20), title, fill='#94a3b8')
    draw.rectangle([width-240, 12, width-20, 42], fill='#1e293b', outline='#334155')
    draw.text((width-225, 20), "Connecté : Admin (Directeur)", fill='#38bdf8')

def draw_sidebar(draw, height, active_idx=0):
    draw.rectangle([0, 55, 230, height], fill='#0b1329')
    menus = [
        "Tableau de Bord",
        "Caisse Enregistreuse POS",
        "Catalogue & Articles",
        "Stocks & Inventaires",
        "Ventes & Factures",
        "Achats & Fournisseurs",
        "Clôtures & Rapport Z",
        "Rapports & TVA (18%)",
        "Assistant Décisionnel IA",
        "Configuration Société"
    ]
    for idx, m in enumerate(menus):
        y = 75 + idx * 48
        if idx == active_idx:
            draw.rectangle([10, y-4, 220, y+34], fill='#0284c7')
            draw.text((25, y+8), m, fill='#ffffff')
        else:
            draw.text((25, y+8), m, fill='#94a3b8')

# 1. CATALOG SCREENSHOT
def make_catalog_screenshot(path):
    w, h = 1200, 680
    im = Image.new('RGB', (w, h), color='#f8fafc')
    draw = ImageDraw.Draw(im)
    draw_topbar(draw, w, "Gestion du Catalogue & Fiches Produits")
    draw_sidebar(draw, h, 2)

    # Content
    draw.text((255, 75), "Catalogue des Articles & Produits", fill='#0f172a')
    draw.text((255, 102), "Configuration des prix de vente (FCFA), taux de TVA (18%) et seuils d'alerte", fill='#64748b')

    # Action bar
    draw.rectangle([255, 135, 650, 175], fill='#ffffff', outline='#cbd5e1')
    draw.text((270, 147), "🔍 Filtrer par nom, référence SKU ou code-barres...", fill='#94a3b8')
    draw.rectangle([980, 135, 1170, 175], fill='#0284c7')
    draw.text((1000, 147), "+ Nouvel Article", fill='#ffffff')

    # Table
    draw.rectangle([255, 195, 1170, 650], fill='#ffffff', outline='#e2e8f0')
    cols = [("Code SKU", 270), ("Désignation Article", 400), ("Catégorie", 640), ("Prix Vente (FCFA)", 780), ("TVA", 930), ("Stock Actuel", 1020), ("Statut", 1110)]
    draw.rectangle([255, 195, 1170, 235], fill='#f1f5f9')
    for c, x in cols:
        draw.text((x, 207), c, fill='#0f172a')

    items = [
        ("LAPTOP-HP-01", "Ordinateur Portable HP ProBook 15 G8", "Informatique", "420 000 FCFA", "18%", "8 pcs", "En stock", '#16a34a'),
        ("MOUSE-WL-01", "Souris Optique Sans Fil Ergonomique", "Accessoires", "8 500 FCFA", "18%", "24 pcs", "En stock", '#16a34a'),
        ("USB-64-KG", "Clé USB 3.0 64Go Kingston", "Stockage", "7 000 FCFA", "18%", "45 pcs", "En stock", '#16a34a'),
        ("PAP-A4-DA", "Carton Papier A4 80g Double A", "Bureautique", "22 500 FCFA", "18%", "2 cartons", "Alerte min", '#dc2626'),
        ("TONER-HP-85A", "Cartouche Toner Laser HP 85A Noir", "Consommables", "35 000 FCFA", "18%", "3 pcs", "Alerte min", '#dc2626'),
        ("KB-USB-LOG", "Clavier Azerty USB Filaire Logitech", "Périphériques", "12 500 FCFA", "18%", "16 pcs", "En stock", '#16a34a'),
        ("ECR-DELL-24", "Écran Dell 24 pouces Full HD HDMI", "Moniteurs", "95 000 FCFA", "18%", "6 pcs", "En stock", '#16a34a'),
    ]
    for idx, r in enumerate(items):
        ry = 245 + idx * 52
        draw.text((270, ry), r[0], fill='#0284c7')
        draw.text((400, ry), r[1], fill='#1e293b')
        draw.text((640, ry), r[2], fill='#64748b')
        draw.text((780, ry), r[3], fill='#0f172a')
        draw.text((930, ry), r[4], fill='#64748b')
        draw.text((1020, ry), r[5], fill='#0f172a')
        draw.rectangle([1100, ry-4, 1165, ry+20], fill='#f0fdf4' if r[7]=='#16a34a' else '#fef2f2')
        draw.text((1108, ry), r[6], fill=r[7])
        draw.line([255, ry+32, 1170, ry+32], fill='#f1f5f9')

    im.save(path, quality=95)

# 2. INVENTORY & STOCK SCREENSHOT
def make_inventory_screenshot(path):
    w, h = 1200, 680
    im = Image.new('RGB', (w, h), color='#f8fafc')
    draw = ImageDraw.Draw(im)
    draw_topbar(draw, w, "Gestion des Dépôts, Mouvements & Alertes Ruptures")
    draw_sidebar(draw, h, 3)

    draw.text((255, 75), "État des Stocks & Mouvements d'Entrepôt", fill='#0f172a')
    draw.text((255, 102), "Surveillance des seuils critiques, valorisation PUMP et ajustements d'inventaire", fill='#64748b')

    # KPI Row
    stk_kpis = [
        ("Valeur Totale du Stock", "64 250 000 FCFA", "Valorisé au coût d'achat", '#eff6ff', '#0284c7'),
        ("Références Actives", "324 articles", "Dans 2 dépôts distincts", '#f0fdf4', '#16a34a'),
        ("Alertes de Réapprovisionnement", "4 références", "Seuil critique franchi", '#fef2f2', '#dc2626'),
    ]
    for idx, (t, v, s, bg, clr) in enumerate(stk_kpis):
        x = 255 + idx * 310
        draw.rectangle([x, 135, x+295, 215], fill=bg, outline='#cbd5e1')
        draw.text((x+15, 147), t, fill='#475569')
        draw.text((x+15, 168), v, fill=clr)
        draw.text((x+15, 195), s, fill='#64748b')

    # Movement History Table
    draw.rectangle([255, 235, 1170, 650], fill='#ffffff', outline='#e2e8f0')
    draw.rectangle([255, 235, 1170, 275], fill='#f1f5f9')
    m_cols = [("Date / Heure", 270), ("Type de Mouvement", 410), ("Article & SKU", 570), ("Quantité", 820), ("Dépôt Source / Dest.", 930), ("Auteur", 1080)]
    for c, x in m_cols:
        draw.text((x, 247), c, fill='#0f172a')

    movs = [
        ("21/09/2026 10:14", "SORTIE VENTE POS", "Ordinateur HP ProBook 15 G8", "- 1 unité", "Dépôt Ouaga Central", "Caissier 1"),
        ("21/09/2026 09:45", "ENTRÉE ACHAT FOURN.", "Papier A4 80g Double A", "+ 50 cartons", "Entrepôt Logistique", "Admin Gérant"),
        ("20/09/2026 17:30", "SORTIE VENTE POS", "Souris Optique Sans Fil", "- 2 unités", "Dépôt Ouaga Central", "Caissier 2"),
        ("20/09/2026 15:20", "TRANSFERT INTER-DÉPÔT", "Clé USB 3.0 64Go", "10 unités", "Logistique -> Ouaga C.", "Gestionnaire"),
        ("20/09/2026 11:00", "AJUSTEMENT INVENTAIRE", "Cartouche Toner Laser HP 85A", "- 1 unité (Casse)", "Dépôt Ouaga Central", "Admin Gérant"),
    ]
    for idx, m in enumerate(movs):
        my = 285 + idx * 52
        draw.text((270, my), m[0], fill='#64748b')
        draw.rectangle([405, my-4, 550, my+20], fill='#eff6ff' if 'ENTRÉE' in m[1] else ('#fef2f2' if 'SORTIE' in m[1] else '#f1f5f9'))
        draw.text((410, my), m[1], fill='#0284c7' if 'ENTRÉE' in m[1] else ('#dc2626' if 'SORTIE' in m[1] else '#475569'))
        draw.text((570, my), m[2], fill='#0f172a')
        draw.text((820, my), m[3], fill='#dc2626' if '-' in m[3] else ('#16a34a' if '+' in m[3] else '#0284c7'))
        draw.text((930, my), m[4], fill='#64748b')
        draw.text((1080, my), m[5], fill='#0f172a')
        draw.line([255, my+32, 1170, my+32], fill='#f1f5f9')

    im.save(path, quality=95)

# 3. CASH CLOSURE & REPORT Z SCREENSHOT
def make_closure_screenshot(path):
    w, h = 1200, 680
    im = Image.new('RGB', (w, h), color='#f8fafc')
    draw = ImageDraw.Draw(im)
    draw_topbar(draw, w, "Clôture de Caisse Journalière & Rapport Z Officiel")
    draw_sidebar(draw, h, 6)

    draw.text((255, 75), "Session de Caisse #CS-2026-09-21-01", fill='#0f172a')
    draw.text((255, 102), "Contrôle des encaissements, recomptage physique et émission du Rapport Z non modifiable", fill='#64748b')

    # Left: Cash count input
    draw.rectangle([255, 135, 680, 650], fill='#ffffff', outline='#cbd5e1')
    draw.rectangle([255, 135, 680, 175], fill='#f1f5f9')
    draw.text((270, 147), "1. Recomptage des Espèces Physiques (Tiroir-caisse)", fill='#0f172a')

    denoms = [
        ("Billets 10 000 FCFA", "150 billets", "1 500 000 FCFA"),
        ("Billets 5 000 FCFA", "80 billets", "400 000 FCFA"),
        ("Billets 2 000 FCFA", "50 billets", "100 000 FCFA"),
        ("Billets 1 000 FCFA", "60 billets", "60 000 FCFA"),
        ("Pièces 500 FCFA", "40 pièces", "20 000 FCFA"),
        ("Pièces 100/200/25/50 FCFA", "Total pièces", "14 500 FCFA"),
    ]
    for idx, (d, q, t) in enumerate(denoms):
        dy = 190 + idx * 46
        draw.text((270, dy), d, fill='#334155')
        draw.text((470, dy), q, fill='#64748b')
        draw.text((580, dy), t, fill='#0f172a')
        draw.line([270, dy+32, 665, dy+32], fill='#f1f5f9')

    draw.rectangle([270, 480, 665, 530], fill='#eff6ff', outline='#bfdbfe')
    draw.text((285, 495), "Total Espèces Compté :", fill='#1e3a8a')
    draw.text((520, 493), "2 094 500 FCFA", fill='#0284c7')

    draw.rectangle([270, 560, 665, 610], fill='#dc2626')
    draw.text((370, 575), "VALIDER & CLÔTURER LA SESSION (Z)", fill='#ffffff')

    # Right: Summary & Z-Report Preview
    draw.rectangle([705, 135, 1170, 650], fill='#ffffff', outline='#cbd5e1')
    draw.rectangle([705, 135, 1170, 175], fill='#f1f5f9')
    draw.text((720, 147), "2. Récapitulatif Théorique & Rapprochement Fiscal", fill='#0f172a')

    z_lines = [
        ("Fond de caisse initial :", "50 000 FCFA"),
        ("Total Ventes Espèces (Cash) :", "2 044 500 FCFA"),
        ("Total Orange Money :", "680 000 FCFA"),
        ("Total Moov Money :", "340 000 FCFA"),
        ("Total Ventes Wave :", "215 000 FCFA"),
        ("Total Cartes Bancaires :", "150 000 FCFA"),
        ("CHIFFRE D'AFFAIRES DU JOUR :", "3 429 500 FCFA"),
        ("Dont TVA 18% Collectée :", "523 144 FCFA"),
        ("Total Théorique Espèces :", "2 094 500 FCFA"),
        ("ÉCART DE CAISSE CONSTATÉ :", "0 FCFA (PARFAIT)"),
    ]
    for idx, (lbl, val) in enumerate(z_lines):
        zy = 195 + idx * 40
        if "CHIFFRE" in lbl or "ÉCART" in lbl:
            draw.rectangle([720, zy-4, 1155, zy+30], fill='#f0fdf4')
            draw.text((730, zy+4), lbl, fill='#16a34a')
            draw.text((1020, zy+4), val, fill='#16a34a')
        else:
            draw.text((730, zy), lbl, fill='#475569')
            draw.text((1020, zy), val, fill='#0f172a')
        draw.line([720, zy+32, 1155, zy+32], fill='#f8fafc')

    draw.rectangle([720, 595, 1155, 635], fill='#0284c7')
    draw.text((850, 607), "🖨️ Imprimer Rapport Z (Ticket 80mm)", fill='#ffffff')

    im.save(path, quality=95)

make_catalog_screenshot('/home/user/NEXORA/docs/screenshots/04_catalog.png')
make_inventory_screenshot('/home/user/NEXORA/docs/screenshots/05_inventory.png')
make_closure_screenshot('/home/user/NEXORA/docs/screenshots/06_closure_z.png')

make_catalog_screenshot('/home/user/NEXORA/frontend/public/docs/screenshots/04_catalog.png')
make_inventory_screenshot('/home/user/NEXORA/frontend/public/docs/screenshots/05_inventory.png')
make_closure_screenshot('/home/user/NEXORA/frontend/public/docs/screenshots/06_closure_z.png')

print("All 6 screenshots successfully rendered!")
