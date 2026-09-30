import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs('/home/user/NEXORA/docs/screenshots', exist_ok=True)
os.makedirs('/home/user/NEXORA/frontend/public/docs/screenshots', exist_ok=True)

def create_dashboard_mockup(path):
    width, height = 1200, 680
    im = Image.new('RGB', (width, height), color='#f8fafc')
    draw = ImageDraw.Draw(im)

    # Topbar
    draw.rectangle([0, 0, width, 60], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.rectangle([20, 16, 120, 44], fill='#0284c7')
    draw.text((32, 22), "NEXORA", fill='#ffffff')
    draw.rectangle([160, 14, 460, 46], fill='#f1f5f9', outline='#cbd5e1')
    draw.text((180, 22), "Rechercher produit, vente, client... (Ctrl+K)", fill='#64748b')
    draw.rectangle([980, 14, 1180, 46], fill='#0284c7')
    draw.text((1000, 22), "+ Ouvrir Caisse (F8)", fill='#ffffff')

    # Sidebar
    draw.rectangle([0, 60, 220, height], fill='#0f172a')
    menus = ["Tableau de bord", "Caisse POS [F8]", "Articles & Catalogue", "Stocks & Inventaire", "Ventes & Factures", "Fournisseurs & Achats", "Rapports Financiers", "Assistant IA", "Parametres"]
    for i, m in enumerate(menus):
        y = 90 + i * 45
        if i == 0:
            draw.rectangle([10, y-6, 210, y+30], fill='#0284c7')
            draw.text((30, y+4), m, fill='#ffffff')
        else:
            draw.text((30, y+4), m, fill='#94a3b8')

    # Main Header
    draw.text((250, 85), "Tableau de Bord de Gestion", fill='#0f172a')
    draw.text((250, 115), "Synthese financiere en temps reel - Franc CFA (FCFA / XOF)", fill='#64748b')

    # 4 KPI Cards
    kpis = [
        ("Chiffre d'Affaires (30j)", "24 850 000 FCFA", "+14.2% ce mois", '#eff6ff', '#0284c7'),
        ("Marge Brute Realisee", "8 650 000 FCFA", "+8.6% marge nette", '#f0fdf4', '#16a34a'),
        ("Articles en Stock", "1 840 unites", "Reparties sur 2 depots", '#f8fafc', '#475569'),
        ("Alertes Rupture", "3 produits", "Action requise", '#fef2f2', '#dc2626'),
    ]
    for i, (tit, val, sub, bg, col) in enumerate(kpis):
        x = 250 + i * 230
        draw.rectangle([x, 150, x+215, 240], fill=bg, outline='#e2e8f0', width=1)
        draw.text((x+15, 162), tit, fill='#475569')
        draw.text((x+15, 185), val, fill=col)
        draw.text((x+15, 215), sub, fill='#64748b')

    # Chart Area
    draw.rectangle([250, 260, 850, 640], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.text((270, 280), "Evolution Hebdomadaire des Ventes (FCFA)", fill='#0f172a')
    days = [("Lun", 70), ("Mar", 110), ("Mer", 90), ("Jeu", 140), ("Ven", 180), ("Sam", 240), ("Dim", 100)]
    for idx, (d, h) in enumerate(days):
        bx = 310 + idx * 75
        by = 580 - h
        draw.rectangle([bx, by, bx+40, 580], fill='#0284c7')
        draw.text((bx+8, 595), d, fill='#64748b')

    # Alerts Area
    draw.rectangle([870, 260, 1170, 640], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.text((890, 280), "Alertes de Reapprovisionnement", fill='#0f172a')
    alerts = [
        ("HP ProBook 15 G8", "2 pcs restantes (Seuil: 5)", '#dc2626'),
        ("Souris Sans Fil Optique", "4 pcs restantes (Seuil: 10)", '#dc2626'),
        ("Papier A4 Double A", "12 rames restantes (Seuil: 20)", '#ea580c'),
    ]
    for idx, (p, desc, clr) in enumerate(alerts):
        ay = 330 + idx * 75
        draw.rectangle([890, ay, 1150, ay+60], fill='#f8fafc', outline='#e2e8f0')
        draw.text((905, ay+10), p, fill='#0f172a')
        draw.text((905, ay+32), desc, fill=clr)

    im.save(path, quality=95)

def create_pos_mockup(path):
    width, height = 1200, 680
    im = Image.new('RGB', (width, height), color='#f1f5f9')
    draw = ImageDraw.Draw(im)

    # Topbar POS
    draw.rectangle([0, 0, width, 55], fill='#0f172a')
    draw.text((20, 18), "NEXORA POS - Caisse Principale", fill='#ffffff')
    draw.text((320, 18), "Session ouverte par : Traore Amadou (Caissier)", fill='#94a3b8')
    draw.rectangle([980, 10, 1180, 45], fill='#dc2626')
    draw.text((1000, 18), "Cloturer Caisse (Z)", fill='#ffffff')

    # Left: Products Grid (65% width)
    draw.rectangle([20, 75, 750, 660], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.rectangle([40, 95, 730, 135], fill='#f8fafc', outline='#cbd5e1')
    draw.text((60, 107), "Scanner un code-barres [F2] ou saisir le nom de l'article...", fill='#64748b')

    # Products Tiles
    products = [
        ("Ordinateur HP 15", "420 000 FCFA", "Stock: 8"),
        ("Souris Sans Fil", "8 500 FCFA", "Stock: 24"),
        ("Cle USB 64Go", "7 000 FCFA", "Stock: 45"),
        ("Clavier Azerty USB", "12 500 FCFA", "Stock: 15"),
        ("Ecran Dell 24 pouces", "95 000 FCFA", "Stock: 6"),
        ("Imprimante HP Laser", "165 000 FCFA", "Stock: 3"),
    ]
    for idx, (name, price, stk) in enumerate(products):
        row = idx // 3
        col = idx % 3
        tx = 40 + col * 230
        ty = 160 + row * 150
        draw.rectangle([tx, ty, tx+215, ty+130], fill='#f8fafc', outline='#cbd5e1', width=1)
        draw.rectangle([tx+10, ty+10, tx+205, ty+65], fill='#e2e8f0')
        draw.text((tx+15, ty+75), name, fill='#0f172a')
        draw.text((tx+15, ty+95), price, fill='#0284c7')
        draw.text((tx+130, ty+95), stk, fill='#16a34a')

    # Right: Order Cart & Payment (35% width)
    draw.rectangle([780, 75, 1180, 660], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.text((800, 95), "Ticket de Caisse en Cours", fill='#0f172a')
    draw.text((800, 120), "Client : Comptoir (Passage)", fill='#64748b')

    cart_items = [
        ("Ordinateur HP 15", "1x", "420 000 FCFA"),
        ("Souris Sans Fil Rechargeable", "2x", "17 000 FCFA"),
        ("Cle USB 64Go Kingston", "1x", "7 000 FCFA"),
    ]
    for idx, (it, q, pr) in enumerate(cart_items):
        cy = 160 + idx * 50
        draw.rectangle([800, cy, 1160, cy+40], fill='#f8fafc')
        draw.text((815, cy+12), f"{q} {it}", fill='#0f172a')
        draw.text((1050, cy+12), pr, fill='#0284c7')

    # Total & Pay section
    draw.rectangle([800, 360, 1160, 480], fill='#f1f5f9')
    draw.text((820, 380), "Sous-total :", fill='#64748b')
    draw.text((1040, 380), "444 000 FCFA", fill='#0f172a')
    draw.text((820, 405), "TVA (18% UEMOA) :", fill='#64748b')
    draw.text((1055, 405), "79 920 FCFA", fill='#64748b')
    draw.text((820, 440), "TOTAL NET A PAYER :", fill='#0f172a')
    draw.text((990, 435), "523 920 FCFA", fill='#16a34a')

    # Payment Methods Buttons
    pay_methods = ["Especes (Cash)", "Orange Money", "Moov Money", "Wave"]
    for idx, pm in enumerate(pay_methods):
        px = 800 + (idx % 2) * 185
        py = 500 + (idx // 2) * 45
        draw.rectangle([px, py, px+175, py+38], fill='#f8fafc', outline='#cbd5e1')
        draw.text((px+20, py+12), pm, fill='#0f172a')

    # Big Green Pay Button
    draw.rectangle([800, 600, 1160, 645], fill='#16a34a')
    draw.text((910, 614), "VALIDER & IMPRIMER TICKET (F8)", fill='#ffffff')

    im.save(path, quality=95)

def create_reports_mockup(path):
    width, height = 1200, 680
    im = Image.new('RGB', (width, height), color='#f8fafc')
    draw = ImageDraw.Draw(im)

    # Topbar
    draw.rectangle([0, 0, width, 60], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.rectangle([20, 16, 120, 44], fill='#0284c7')
    draw.text((320, 22), "NEXORA Business Intelligence - Rapports & Fiscalite UEMOA", fill='#0f172a')

    # Sidebar
    draw.rectangle([0, 60, 220, height], fill='#0f172a')
    menus = ["Tableau de bord", "Caisse POS", "Articles & Catalogue", "Stocks & Inventaire", "Ventes & Factures", "Fournisseurs & Achats", "Rapports Financiers", "Assistant IA", "Parametres"]
    for i, m in enumerate(menus):
        y = 90 + i * 45
        if i == 6:
            draw.rectangle([10, y-6, 210, y+30], fill='#0284c7')
            draw.text((30, y+4), m, fill='#ffffff')
        else:
            draw.text((30, y+4), m, fill='#94a3b8')

    draw.text((250, 85), "Rapports Financiers & Declaration de TVA", fill='#0f172a')
    draw.text((250, 115), "Etats consolidés pour la direction generale et l'administration fiscale (DGI)", fill='#64748b')

    # Financial Summary Table
    draw.rectangle([250, 160, 1170, 640], fill='#ffffff', outline='#e2e8f0', width=1)
    headers = [("Periode", 270), ("Ventes TTC (FCFA)", 430), ("TVA Collectee 18%", 610), ("Achats TTC (FCFA)", 790), ("Marge Nette (FCFA)", 980)]
    for h, x in headers:
        draw.text((x, 180), h, fill='#0f172a')
    draw.line([250, 210, 1170, 210], fill='#cbd5e1', width=1)

    rows = [
        ("Janvier 2026", "28 450 000 FCFA", "4 339 830 FCFA", "18 200 000 FCFA", "5 910 170 FCFA"),
        ("Fevrier 2026", "31 200 000 FCFA", "4 759 322 FCFA", "19 800 000 FCFA", "6 640 678 FCFA"),
        ("Mars 2026", "34 800 000 FCFA", "5 308 474 FCFA", "21 500 000 FCFA", "8 191 526 FCFA"),
        ("Total 1er Trimestre", "94 450 000 FCFA", "14 407 626 FCFA", "59 500 000 FCFA", "20 742 374 FCFA"),
    ]
    for idx, r in enumerate(rows):
        ry = 230 + idx * 55
        if idx == 3:
            draw.rectangle([250, ry-10, 1170, ry+35], fill='#f0fdf4')
            draw.text((270, ry), r[0], fill='#16a34a')
            for c_idx in range(1, 5):
                draw.text((headers[c_idx][1], ry), r[c_idx], fill='#16a34a')
        else:
            draw.text((270, ry), r[0], fill='#475569')
            for c_idx in range(1, 5):
                draw.text((headers[c_idx][1], ry), r[c_idx], fill='#0f172a')
            draw.line([250, ry+40, 1170, ry+40], fill='#f1f5f9', width=1)

    im.save(path, quality=95)

create_dashboard_mockup('/home/user/NEXORA/docs/screenshots/01_dashboard.png')
create_pos_mockup('/home/user/NEXORA/docs/screenshots/02_pos.png')
create_reports_mockup('/home/user/NEXORA/docs/screenshots/03_reports.png')

# Duplicate to frontend public folder for immediate browser serving
create_dashboard_mockup('/home/user/NEXORA/frontend/public/docs/screenshots/01_dashboard.png')
create_pos_mockup('/home/user/NEXORA/frontend/public/docs/screenshots/02_pos.png')
create_reports_mockup('/home/user/NEXORA/frontend/public/docs/screenshots/03_reports.png')

print("Mockup screenshots generated successfully!")
