# -*- coding: utf-8 -*-
"""Correctif v2 du bilan PDF individuel : periode exacte, contenu exhaustif.

La version v1 du bilan gardait le filtre vendeur et la date de fin, mais la
ventilation produit etait encore tronquee a six lignes. Plusieurs KPI etaient
calcules puis jetes. Le correcteur v2 retire ces limites, conserve les produits
distincts meme s'ils portent le meme nom et imprime toutes les pages necessaires.
Il lie aussi explicitement l'export au compte connecte par defaut.

Usage depuis la racine du projet :
    py corriger_etat_vendeur_pdf.py --verifier
    py corriger_etat_vendeur_pdf.py
    py manage.py test tests.test_etat_vendeur_pdf -v 2
"""
from __future__ import print_function

import argparse
import re
import shutil
import sys
from pathlib import Path

DOSSIER_SAUVEGARDE = 'sauvegardes-etat-vendeur'
FICHIER_TEST_REL = Path('fichiers/tests/test_etat_vendeur_pdf.py')
MARQUEURS_BACKEND = (
    '_nexora_agreger_articles',
    '_nexora_produits_tries',
    'kpi_detail_table',
    'repeatRows=1, splitByRow=1',
    'from xml.sax.saxutils import escape',
)

MOTIF_DATE_FAUTIVE = re.compile(
    r'(?P<ind>[ \t]*)if not end_date:\n'
    r'(?P=ind)[ \t]+end_date = now \+ timezone\.timedelta\(days=1\)\n'
    r'(?P=ind)else:\n'
    r'(?:[ \t]*#[^\n]*\n)*'
    r'(?P=ind)[ \t]+end_date = max\(end_date, now \+ timezone\.timedelta\(hours=4\)\)\n'
)

HELPERS = '''\n\ndef _nexora_agreger_articles(sales):\n    """Agrege les lignes sans fusionner deux produits distincts de meme nom."""\n    product_sales = {}\n    total_items_qty = Decimal('0.00')\n    cogs_total = Decimal('0.00')\n\n    for sale in sales:\n        for item in sale.items.all():\n            product = item.product\n            p_name = product.name if product else 'Article divers'\n            p_sku = product.sku if product else '-'\n            cost_p = Decimal(str(product.cost_price or '0.00')) if product else Decimal('0.00')\n            quantity = Decimal(str(item.quantity or '0.00'))\n            line_total = Decimal(str(item.total or '0.00'))\n\n            product_id = getattr(product, 'pk', None) if product else None\n            if product_id is None and product is not None:\n                product_id = getattr(product, 'id', None)\n            product_key = product_id if product_id is not None else (p_sku, p_name)\n\n            total_items_qty += quantity\n            cogs_total += quantity * cost_p\n            if product_key not in product_sales:\n                product_sales[product_key] = {\n                    'name': p_name,\n                    'sku': p_sku,\n                    'qty': Decimal('0.00'),\n                    'revenue': Decimal('0.00'),\n                    'profit': Decimal('0.00'),\n                }\n            product_sales[product_key]['qty'] += quantity\n            product_sales[product_key]['revenue'] += line_total\n            product_sales[product_key]['profit'] += line_total - (quantity * cost_p)\n\n    return product_sales, total_items_qty, cogs_total\n\n\ndef _nexora_produits_tries(product_sales):\n    """Retourne TOUS les produits, du CA le plus eleve au plus faible."""\n    return sorted(\n        product_sales.values(),\n        key=lambda produit: (produit['revenue'], str(produit['name']).casefold(), str(produit['sku'])),\n        reverse=True,\n    )\n\n\ndef _nexora_formater_quantite(valeur):\n    """Affiche les quantites decimales sans arrondir a l'unite."""\n    quantite = Decimal(str(valeur or '0.00'))\n    return format(quantite, ',.2f').replace(',', ' ').rstrip('0').rstrip('.')\n'''

BLOC_KPI = '''        elements.append(kpi_table)\n        elements.append(Spacer(1, 5))\n\n        # Indicateurs complementaires deja calcules : encaissements, taxes,\n        # remises et quantite totale d'articles vendus.\n        kpi_detail_data = [\n            [\n                Paragraph("<b>Montant encaissé</b>", cell_bold),\n                Paragraph("<b>Taxes</b>", cell_bold),\n                Paragraph("<b>Remises</b>", cell_bold),\n                Paragraph("<b>Articles vendus</b>", cell_bold),\n            ],\n            [\n                Paragraph(f"<b>{total_paid:,.0f} FCFA</b>".replace(',', ' '), cell_bold),\n                Paragraph(f"{total_tax:,.0f} FCFA".replace(',', ' '), cell_style),\n                Paragraph(f"{total_discounts:,.0f} FCFA".replace(',', ' '), cell_style),\n                Paragraph(_nexora_formater_quantite(total_items_qty), cell_style),\n            ],\n        ]\n        kpi_detail_table = Table(kpi_detail_data, colWidths=[135, 130, 135, 138])\n        kpi_detail_table.setStyle(TableStyle([\n            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),\n            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),\n            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),\n            ('PADDING', (0, 0), (-1, -1), 5),\n            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),\n        ]))\n        elements.append(kpi_detail_table)\n        elements.append(Spacer(1, 10))\n'''

BLOC_AGREGATION = '''        # Ventilation exhaustive : aucun produit n'est fusionne ou tronque.\n        product_sales, total_items_qty, cogs_total = _nexora_agreger_articles(sales)\n\n'''

BLOC_PRODUITS = '''        p_table_data = [p_table_headers]\n        for p_data in sorted_prods:\n            p_name = escape(str(p_data['name']))\n            p_sku = escape(str(p_data['sku'] or '-'))\n            share = (p_data['revenue'] / total_revenue * Decimal('100')).quantize(Decimal('0.1')) if total_revenue > 0 else Decimal('0.0')\n            p_table_data.append([\n                Paragraph(p_name, cell_style),\n                Paragraph(p_sku, cell_style),\n                Paragraph(_nexora_formater_quantite(p_data['qty']), cell_style),\n                Paragraph(f"{p_data['revenue']:,.0f} FCFA".replace(',', ' '), cell_bold),\n                Paragraph(f"{p_data['profit']:,.0f} FCFA".replace(',', ' '), cell_bold),\n                Paragraph(f"{share}%", cell_style),\n            ])\n\n        if not sorted_prods:\n            p_table_data.append([\n                Paragraph("Aucun article vendu sur cette période.", cell_style),\n                Paragraph("", cell_style), Paragraph("", cell_style),\n                Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style),\n            ])\n\n        p_table = Table(p_table_data, colWidths=[180, 80, 70, 85, 80, 43], repeatRows=1, splitByRow=1)\n'''

POS_QUERY_OLD = '''  const handleExportSellerPdf = async () => {\n    try {\n      setIsExportingSellerPdf(true);\n      const queryParams = new URLSearchParams({\n        start_date: sellerPdfPeriod.start_date,\n        end_date: sellerPdfPeriod.end_date,\n        ...(sellerPdfPeriod.seller_id\n          ? { seller_id: sellerPdfPeriod.seller_id }\n          : sellerPdfPeriod.seller_email\n            ? { seller: sellerPdfPeriod.seller_email }\n            : {}),\n      });\n'''

POS_QUERY_NEW = '''  const getSellerPdfQueryParams = () => {\n    // Ne jamais laisser le parametre vendeur vide : le PDF est celui du\n    // compte connecte par defaut, sauf selection explicite d'un responsable.\n    const sellerId = sellerPdfPeriod.seller_id || String((authUser as any)?.id || '');\n    const sellerEmail = sellerPdfPeriod.seller_email || authUser?.email || '';\n    return new URLSearchParams({\n      start_date: sellerPdfPeriod.start_date,\n      end_date: sellerPdfPeriod.end_date,\n      ...(sellerId ? { seller_id: sellerId } : sellerEmail ? { seller: sellerEmail } : {}),\n    });\n  };\n\n  const handleExportSellerPdf = async () => {\n    try {\n      if (!(authUser as any)?.id) {\n        throw new Error('Compte vendeur non identifié. Reconnectez-vous puis réessayez.');\n      }\n      setIsExportingSellerPdf(true);\n      const queryParams = getSellerPdfQueryParams();\n'''


def _decode_text(path):
    raw = path.read_bytes()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    newline = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), bom, newline


def _encode_text(text, bom, newline):
    body = text.replace('\n', newline).encode('utf-8')
    return (b'\xef\xbb\xbf' if bom else b'') + body


def _find_backend(root):
    expected = root / 'apps' / 'sales' / 'pdf_seller_report.py'
    if expected.is_file():
        return expected
    candidates = []
    for path in root.rglob('pdf_seller_report.py'):
        parts = {p.lower() for p in path.parts}
        if parts & {'.git', 'node_modules', '.next', '.venv', 'venv', 'build', 'dist'}:
            continue
        if any(p.lower().startswith('sauvegardes-') for p in path.parts):
            continue
        if 'correctif-etat-vendeur' in parts or 'telechargements' in parts:
            continue
        try:
            txt = path.read_text(encoding='utf-8-sig')
        except Exception:
            continue
        if 'class SellerSalesReportPdfView' in txt and 'export-seller-pdf' in txt:
            candidates.append(path)
    if len(candidates) == 1:
        return candidates[0]
    return None


def _find_pos(root):
    expected_paths = (
        root / 'frontend' / 'src' / 'app' / 'pos' / 'page.tsx',
        root / 'app' / 'pos' / 'page.tsx',
    )
    for path in expected_paths:
        if path.is_file():
            text, _, _ = _decode_text(path)
            if 'Mon Bilan Vente PDF' in text and 'handleExportSellerPdf' in text:
                return path
    candidates = []
    for path in root.rglob('page.tsx'):
        parts = {p.lower() for p in path.parts}
        if parts & {'.git', 'node_modules', '.next', '.venv', 'venv', 'build', 'dist'}:
            continue
        if any(p.lower().startswith('sauvegardes-') for p in path.parts):
            continue
        if 'correctif-etat-vendeur' in parts or 'telechargements' in parts:
            continue
        try:
            text, _, _ = _decode_text(path)
        except Exception:
            continue
        if 'Mon Bilan Vente PDF' in text and 'handleExportSellerPdf' in text:
            candidates.append(path)
    if len(candidates) == 1:
        return candidates[0]
    return None


def _patch_backend(source):
    actions = []
    original = source

    # 1. Respecter la date de fin demandee, y compris sur les copies anterieures.
    if 'timezone.timedelta(hours=4)' in source:
        source, count = MOTIF_DATE_FAUTIVE.subn(
            lambda match: (match.group('ind') + 'if not end_date:\n'
                           + match.group('ind') + '    end_date = now + timezone.timedelta(days=1)\n'
                           + match.group('ind') + '# La date de fin choisie est respectee telle quelle : elle couvre deja\n'
                           + match.group('ind') + '# toute la journee selectionnee (23:59:59). L\'ancien code la remplacait\n'
                           + match.group('ind') + '# par « maintenant + 4 h » : un rapport demande sur une periode passee\n'
                           + match.group('ind') + '# contenait alors toutes les ventes enregistrees depuis.\n'),
            source,
            count=1,
        )
        if count != 1:
            raise ValueError("date de fin : bloc 'maintenant + 4 h' non reconnu; aucun fichier ne sera modifie")
        actions.append('date de fin de periode respectee')
    else:
        actions.append('date de fin deja correcte')

    # 2. Ajouter les utilitaires exhaustifs du rapport si absents.
    if '_nexora_agreger_articles' not in source:
        start = '        # Product breakdown\n'
        end = '        gross_margin = total_revenue - cogs_total\n'
        if source.count(start) != 1 or source.count(end) != 1:
            raise ValueError('bloc de ventilation des produits inconnu; aucun fichier ne sera modifie')
        i, j = source.index(start), source.index(end)
        ancien = source[i:j]
        attendus = ('product_sales = {}', 'total_items_qty =', 'item.total', 'p_name not in product_sales')
        if not all(part in ancien for part in attendus):
            raise ValueError('contenu de ventilation different de la version verifiee; aucun fichier ne sera modifie')
        source = source[:i] + BLOC_AGREGATION + source[j:]
        class_anchor = '\n\nclass SellerSalesReportPdfView(APIView):'
        if source.count(class_anchor) != 1:
            raise ValueError('emplacement des fonctions vendeur inconnu; aucun fichier ne sera modifie')
        source = source.replace(class_anchor, HELPERS + class_anchor, 1)
        if 'from xml.sax.saxutils import escape\n' not in source:
            if source.count('from decimal import Decimal\n') != 1:
                raise ValueError('import Decimal introuvable; aucun fichier ne sera modifie')
            source = source.replace('from decimal import Decimal\n',
                                    'from decimal import Decimal\nfrom xml.sax.saxutils import escape\n', 1)
        actions.append('agregation par identifiant produit installee')
    else:
        if not all(marker in source for marker in MARQUEURS_BACKEND[:2]):
            raise ValueError('correctif partiel des produits detecte; aucun fichier ne sera modifie')
        actions.append('agregation exhaustive deja installee')

    # 3. Afficher les indicateurs deja calcules et supprimer le plafond de six.
    if 'kpi_detail_table' not in source:
        anchor = '        elements.append(kpi_table)\n        elements.append(Spacer(1, 10))\n'
        if source.count(anchor) != 1:
            raise ValueError('emplacement des indicateurs PDF inconnu; aucun fichier ne sera modifie')
        source = source.replace(anchor, BLOC_KPI, 1)
        actions.append('indicateurs encaisses/taxes/remises/unites affiches')
    else:
        actions.append('indicateurs complementaires deja affiches')

    if 'for p_name, p_data in sorted_prods[:6]:' in source:
        source = source.replace(
            'sorted_prods = sorted(product_sales.items(), key=lambda x: x[1][\'revenue\'], reverse=True)',
            'sorted_prods = _nexora_produits_tries(product_sales)',
            1,
        )
        source = source.replace(
            'top_prod_name, top_prod_data = sorted_prods[0]',
            "top_prod_data = sorted_prods[0]\n            top_prod_name = escape(str(top_prod_data['name']))",
            1,
        )
        old_qty = "{top_prod_data['qty']:,.0f} unité(s) vendue(s)"
        if source.count(old_qty) != 1:
            raise ValueError('quantite du produit phare non reconnue; aucun fichier ne sera modifie')
        source = source.replace(old_qty,
                                "{_nexora_formater_quantite(top_prod_data['qty'])} unité(s) vendue(s)", 1)
        old_table = '''        p_table_data = [p_table_headers]\n        for p_name, p_data in sorted_prods[:6]:\n            share = (p_data['revenue'] / total_revenue * Decimal('100')).quantize(Decimal('0.1')) if total_revenue > 0 else Decimal('0.0')\n            p_table_data.append([\n                Paragraph(p_name, cell_style),\n                Paragraph(p_data['sku'], cell_style),\n                Paragraph(f"{p_data['qty']:,.0f}".replace(',', ' '), cell_style),\n                Paragraph(f"{p_data['revenue']:,.0f} FCFA".replace(',', ' '), cell_bold),\n                Paragraph(f"{p_data['profit']:,.0f} FCFA".replace(',', ' '), cell_bold),\n                Paragraph(f"{share}%", cell_style),\n            ])\n\n        p_table = Table(p_table_data, colWidths=[180, 80, 70, 85, 80, 43])\n'''
        if source.count(old_table) != 1:
            raise ValueError('tableau des produits (plafond six) non reconnu; aucun fichier ne sera modifie')
        source = source.replace(old_table, BLOC_PRODUITS, 1)
        ancien_resume = 'items_summary = f"{sum([it.quantity for it in s.items.all()], Decimal(\'0.00\')):,.0f} art."'
        if source.count(ancien_resume) != 1:
            raise ValueError('resume des quantites par facture non reconnu; aucun fichier ne sera modifie')
        source = source.replace(
            ancien_resume,
            'items_summary = f"{_nexora_formater_quantite(sum((it.quantity for it in s.items.all()), Decimal(\'0.00\')))} art."',
            1,
        )
        ancien_client = 'Paragraph(f"<b>{c_name[:26]}</b>" if s.customer else c_name[:26], cell_style)'
        if source.count(ancien_client) != 1:
            raise ValueError('affichage du client tronque non reconnu; aucun fichier ne sera modifie')
        source = source.replace(
            ancien_client,
            'Paragraph(f"<b>{escape(str(c_name))}</b>" if s.customer else escape(str(c_name)), cell_style)',
            1,
        )
        source = source.replace(
            '        # Top Products table\n',
            '        # Ventilation complete par article (la table continue sur autant de pages\n'
            '        # que necessaire ; son entete est repetee a chaque nouvelle page).\n',
            1,
        )
        source = source.replace(
            '<b>2. Répartition des Ventes par Produit & Contribution à la Marge :</b>',
            '<b>2. Répartition complète des Ventes par Produit & Contribution à la Marge :</b>',
            1,
        )
        actions.append('limite de six produits retiree; tableau pagine sans plafond')
    elif 'for p_data in sorted_prods:' in source and 'splitByRow=1' in source:
        actions.append('tous les produits et pagination deja actifs')
    else:
        raise ValueError('etat inconnu du tableau produit; aucun fichier ne sera modifie')

    source = source.replace(
        'Exports a 2-page customized PDF report for an individual seller/cashier:',
        'Exports a complete, multi-page PDF report for an individual seller/cashier:',
    )
    source = source.replace('PAGE 1 : ÉTAT OFFICIEL DES VENTES DU VENDEUR',
                            'ETAT OFFICIEL DES VENTES DU VENDEUR')
    source = source.replace('PAGE 2 : ANALYSE DES VENTES DU VENDEUR & SUGGESTIONS COMMERCIALES',
                            'ANALYSE DES VENTES DU VENDEUR & SUGGESTIONS COMMERCIALES')

    if 'sorted_prods[:6]' in source or not all(marker in source for marker in MARQUEURS_BACKEND):
        raise ValueError('verification finale du rapport incomplete; aucun fichier ne sera modifie')
    try:
        compile(source, 'apps/sales/pdf_seller_report.py', 'exec')
    except SyntaxError as exc:
        raise ValueError('la vue PDF corrigee ne compile pas (%s); aucun fichier ne sera modifie' % exc)
    return source, actions, source != original


def _patch_pos(source):
    original = source
    actions = []
    if 'getSellerPdfQueryParams' not in source:
        if source.count(POS_QUERY_OLD) != 1:
            raise ValueError('fonction d export POS inconnue; aucun fichier ne sera modifie')
        source = source.replace(POS_QUERY_OLD, POS_QUERY_NEW, 1)
        actions.append('identifiant du vendeur connecte garanti dans la requete')
    else:
        if 'sellerPdfPeriod.seller_id || String((authUser as any)?.id || \'\')' not in source:
            raise ValueError('fallback vendeur incomplet; aucun fichier POS ne sera modifie')
        actions.append('identifiant vendeur deja garanti')

    source = source.replace('Rapport Individuel Vendeur sur 2 Pages :',
                            'Rapport complet du vendeur connecté :')
    ancien_liste = '''<li><strong>Page 1 :</strong> État officiel détaillé de vos ventes sur la période (chiffre d'affaires, panier moyen, factures et règlements).</li>\n              <li><strong>Page 2 :</strong> Analyse automatique de vos performances commerciales avec ventilation par marge et suggestions concrètes d'optimisation.</li>'''
    nouvelle_liste = '''<li><strong>Ventes :</strong> toutes les factures validées de ce vendeur sur la période choisie.</li>\n              <li><strong>Produits :</strong> détail exhaustif, sans limite aux six premiers ; la table continue automatiquement sur plusieurs pages.</li>\n              <li><strong>Indicateurs :</strong> chiffre d'affaires, encaissé, taxes, remises, unités, marge et analyse commerciale.</li>'''
    if ancien_liste in source:
        source = source.replace(ancien_liste, nouvelle_liste, 1)
        actions.append('libelle du rapport mis a jour (pages variables)')
    elif 'la table continue automatiquement sur plusieurs pages' in source:
        actions.append('libelle multi-pages deja actif')
    else:
        raise ValueError('description du bilan POS inconnue; aucun fichier ne sera modifie')

    # Le lien direct fait une requete sans le jeton Bearer ; l application doit
    # utiliser l export authentifie qui fixe explicitement l identifiant vendeur.
    direct_anchor = '            <a\n              href={`/api/v1/sales/export-seller-pdf/?'
    if direct_anchor in source:
        start = source.index(direct_anchor)
        end_marker = '            </a>\n'
        end = source.find(end_marker, start)
        if end < 0:
            raise ValueError('lien PDF direct non reconnu; aucun fichier POS ne sera modifie')
        source = source[:start] + source[end + len(end_marker):]
        actions.append('lien PDF anonyme supprime; export authentifie conserve')
    elif 'Ouvrir dans un onglet (Direct)' not in source:
        actions.append('lien PDF direct deja absent')
    else:
        raise ValueError('lien PDF direct residuel; aucun fichier POS ne sera modifie')

    source = source.replace('Télécharger mon Rapport PDF (2 Pages)',
                            'Télécharger mon Rapport PDF complet')
    if 'Télécharger mon Rapport PDF complet' not in source:
        raise ValueError('bouton PDF complet introuvable; aucun fichier POS ne sera modifie')
    return source, actions, source != original


def _backup_and_write(path, text, backup_root, root):
    old = path.read_bytes()
    bom = old.startswith(b'\xef\xbb\xbf')
    newline = '\r\n' if b'\r\n' in old else '\n'
    new_bytes = _encode_text(text, bom, newline)
    if old == new_bytes:
        return False
    rel = path.relative_to(root)
    backup = backup_root / rel
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(path, backup)
    temp = path.with_name(path.name + '.nexora-tmp')
    temp.write_bytes(new_bytes)
    temp.replace(path)
    return True


def _install_test(root, script_dir):
    source = script_dir / FICHIER_TEST_REL
    target = root / 'tests' / 'test_etat_vendeur_pdf.py'
    if not source.is_file():
        raise ValueError('test integre au ZIP introuvable : %s' % source)
    contenu = source.read_bytes()
    if target.exists() and target.read_bytes() == contenu:
        return 'test complet deja en place'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        ancien = target.with_name('test_etat_vendeur_pdf.py.ancien')
        if not ancien.exists():
            shutil.copy2(target, ancien)
    shutil.copy2(source, target)
    return 'test complet installe (ancienne version conservee en .ancien si presente)'


def appliquer(root, verifier=False):
    root = root.resolve()
    print('=' * 76)
    print('NEXORA — BILAN PDF VENDEUR : contenu exhaustif (correctif v2)')
    print('Projet : %s' % root)
    print('Mode   : %s' % ('verification sans ecriture' if verifier else 'correction'))
    print('=' * 76)

    backend = _find_backend(root)
    pos = _find_pos(root)
    if backend is None or pos is None:
        print('[ANNULE] Couple backend/POS non identifie sans ambiguite.')
        print('  backend : %s' % (backend or 'introuvable ou plusieurs copies actives'))
        print('  POS     : %s' % (pos or 'introuvable ou plusieurs copies actives'))
        print('  Aucun fichier n a ete modifie. Passez --racine avec le dossier du vrai projet.')
        return 2

    print('Backend : %s' % backend.relative_to(root))
    print('POS     : %s' % pos.relative_to(root))
    btext, bbom, bnl = _decode_text(backend)
    ptext, pbom, pnl = _decode_text(pos)
    try:
        bnew, bactions, bchanged = _patch_backend(btext)
        pnew, pactions, pchanged = _patch_pos(ptext)
    except ValueError as exc:
        print('[ANNULE] %s' % exc)
        print('Aucun fichier n a ete modifie.')
        return 2

    script_dir = Path(__file__).resolve().parent
    test_source = script_dir / FICHIER_TEST_REL
    if not test_source.is_file():
        print('[ANNULE] Test de recette absent du paquet : %s' % FICHIER_TEST_REL)
        return 2

    for action in bactions:
        print('  [BACKEND] %s' % action)
    for action in pactions:
        print('  [POS]     %s' % action)

    if verifier:
        print('  [TEST] tests/test_etat_vendeur_pdf.py %s' %
              ('deja a jour' if (root / 'tests' / 'test_etat_vendeur_pdf.py').exists()
               and (root / 'tests' / 'test_etat_vendeur_pdf.py').read_bytes() == test_source.read_bytes()
               else 'sera installe/mis a jour'))
        print('\nAucune modification ecrite.')
        return 0

    backup_root = root / DOSSIER_SAUVEGARDE
    if bchanged:
        _backup_and_write(backend, bnew, backup_root, root)
    if pchanged:
        _backup_and_write(pos, pnew, backup_root, root)
    etat_test = _install_test(root, script_dir)
    print('  [TEST] %s' % etat_test)
    print('  [SAUVEGARDE] %s' % backup_root)
    print('\nControle :')
    print('  py manage.py test tests.test_etat_vendeur_pdf -v 2')
    print('  PDF attendu : toutes les ventes et tous les articles du vendeur choisi,')
    print('  tous les KPI, et autant de pages que necessaire.')
    print('Reexecution : sans effet (idempotent).')
    return 0


def main():
    parser = argparse.ArgumentParser(description='Correctif v2 du bilan PDF vendeur NEXORA')
    parser.add_argument('--racine', help='dossier du vrai projet (defaut : dossier courant)')
    parser.add_argument('--verifier', action='store_true', help='diagnostic, aucune ecriture')
    args = parser.parse_args()
    root = Path(args.racine).resolve() if args.racine else Path.cwd().resolve()
    return appliquer(root, args.verifier)


if __name__ == '__main__':
    sys.exit(main())
