import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # En-tête (pages > 1)
        if self._pageNumber > 1:
            self.drawString(45, 805, "NEXORA ENTERPRISE ERP & POS — Manuel Utilisateur & Guide Pratique Exhaustif")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(45, 798, 550, 798)
        
        # Pied de page
        page_text = f"Page {self._pageNumber} sur {page_count}"
        self.drawRightString(550, 28, page_text)
        self.setFont("Helvetica", 8)
        self.drawString(45, 28, "Édition Afrique de l'Ouest (FCFA / XOF) • Conforme UEMOA & OHADA")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(45, 38, 550, 38)
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    fig_style = ParagraphStyle(
        'FigCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceBefore=3,
        spaceAfter=8
    )

    story = []

    # ==================== PAGE 1 : TITRE, ACCES, DASHBOARD ====================
    story.append(Paragraph("NEXORA ENTERPRISE ERP & POINT DE VENTE (POS)", title_style))
    story.append(Paragraph("Manuel Utilisateur Exhaustif & Guide Opérationnel — Édition UEMOA (FCFA)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=8))

    intro_p = Paragraph("<b>À propos de ce manuel :</b> Ce guide fournit toutes les procédures opérationnelles pour l'exploitation quotidienne de <b>NEXORA</b> : gestion de caisse, stocks, inventaires, clôtures de caisse (Rapport Z) et déclarations fiscales. Le système fonctionne exclusivement en <b>Franc CFA (FCFA)</b> avec le régime standard de <b>TVA à 18%</b> et la compatibilité <b>Mobile Money</b> (Orange Money, Moov Money, Wave).", body_style)
    intro_table = Table([[intro_p]], colWidths=[505])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#bfdbfe')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("1. Accès au Système & Identifiants par Défaut", h1_style))
    story.append(Paragraph("• <b>Adresse Web de l'application & caisse :</b> <font color='#0284c7'>http://localhost:3000</font>", bullet_style))
    story.append(Paragraph("• <b>Portail d'Administration Technique :</b> <font color='#0284c7'>http://localhost:8008/admin/</font>", bullet_style))

    users_data = [
        [Paragraph("<b>Rôle Utilisateur</b>", body_style), Paragraph("<b>Identifiant</b>", body_style), Paragraph("<b>Mot de passe</b>", body_style), Paragraph("<b>Périmètre d'action</b>", body_style)],
        [Paragraph("Directeur / Gérant", body_style), Paragraph("admin", body_style), Paragraph("Admin123456!", body_style), Paragraph("Accès complet : Tableaux de bord, Marges, Stocks, Achats, Clôtures Z, Rapports financiers et TVA", body_style)],
        [Paragraph("Caissier / Vendeur", body_style), Paragraph("cashier", body_style), Paragraph("Cashier123!", body_style), Paragraph("Accès dédié : Caisse POS tactile, encaissement (Cash/Mobile Money), impression tickets et clôture session", body_style)],
    ]
    t_users = Table(users_data, colWidths=[105, 65, 85, 250])
    t_users.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_users)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Le Tableau de Bord Stratégique en Temps Réel", h1_style))
    story.append(Paragraph("Le tableau de bord permet à la direction de visualiser la santé financière en moins de 3 secondes :", body_style))
    story.append(Paragraph("• <b>Chiffre d'Affaires (30j) :</b> Totalité des ventes enregistrées en FCFA avec taux d'évolution mensuel.", bullet_style))
    story.append(Paragraph("• <b>Marge Brute Réalisée :</b> Bénéfice commercial après déduction automatique des coûts d'achat.", bullet_style))
    story.append(Paragraph("• <b>Alertes de Rupture :</b> Nombre précis d'articles sous le seuil d'alerte avec bouton de commande immédiat.", bullet_style))
    story.append(Spacer(1, 3))

    dash_path = "/home/user/NEXORA/docs/screenshots/01_dashboard.png"
    if os.path.exists(dash_path):
        story.append(Image(dash_path, width=500, height=190))
        story.append(Paragraph("Figure 1.0 — Vue d'ensemble du Tableau de bord stratégique NEXORA avec indicateurs consolidés en FCFA", fig_style))

    story.append(PageBreak())

    # ==================== PAGE 2 : CAISSE POS TACTILE & ENCAISSEMENT ====================
    story.append(Paragraph("3. La Caisse Enregistreuse Tactile (Point de Vente / POS)", h1_style))
    story.append(Paragraph("Le module POS est optimisé pour un passage ultra-rapide des clients en magasin ou supermarché :", body_style))
    story.append(Paragraph("1. <b>Ouvrir la session (F8) :</b> Cliquez sur « Ouvrir Caisse » et indiquez votre fond de caisse initial.", bullet_style))
    story.append(Paragraph("2. <b>Ajouter des articles :</b> Scannez le code-barres avec la douchette, cliquez sur les tuiles tactiles ou appuyez sur <b>F2</b> pour chercher par référence.", bullet_style))
    story.append(Paragraph("3. <b>Gestion du Panier :</b> Ajustez les quantités (+ / -) et appliquez les remises autorisées par la direction.", bullet_style))
    story.append(Paragraph("4. <b>Modes d'Encaissement :</b>", bullet_style))
    story.append(Paragraph("   - <b>Espèces (Cash) :</b> Saisissez le montant remis ; NEXORA affiche en grand le rendu de monnaie exact en FCFA.", bullet_style))
    story.append(Paragraph("   - <b>Mobile Money :</b> Sélectionnez <i>Orange Money</i>, <i>Moov Money</i> ou <i>Wave</i> et validez la réception.", bullet_style))
    story.append(Paragraph("   - <b>Carte Bancaire / Chèque :</b> Saisissez le numéro d'autorisation bancaire.", bullet_style))
    story.append(Paragraph("5. <b>Impression du Ticket (F8) :</b> Le ticket thermique 80mm est imprimé et le stock physique est décrémenté.", bullet_style))
    story.append(Spacer(1, 3))

    pos_path = "/home/user/NEXORA/docs/screenshots/02_pos.png"
    if os.path.exists(pos_path):
        story.append(Image(pos_path, width=500, height=195))
        story.append(Paragraph("Figure 2.0 — Interface tactile de la Caisse POS NEXORA (Sélection d'articles et Panneau de règlement)", fig_style))

    # Tableau raccourcis
    short_data = [
        [Paragraph("<b>Raccourci</b>", body_style), Paragraph("<b>Fonction Caissier</b>", body_style), Paragraph("<b>Raccourci</b>", body_style), Paragraph("<b>Fonction Caissier</b>", body_style)],
        [Paragraph("<b>F2</b>", body_style), Paragraph("Recherche instantanée d'article", body_style), Paragraph("<b>F8</b>", body_style), Paragraph("Fenêtre d'encaissement / Valider", body_style)],
        [Paragraph("<b>F4</b>", body_style), Paragraph("Changer de client (Comptoir / Pro)", body_style), Paragraph("<b>F10</b>", body_style), Paragraph("Mettre la vente en attente", body_style)],
    ]
    t_short = Table(short_data, colWidths=[65, 187, 65, 188])
    t_short.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_short)

    story.append(PageBreak())

    # ==================== PAGE 3 : CATALOGUE & STOCKS ====================
    story.append(Paragraph("4. Gestion du Catalogue & Fiches Articles", h1_style))
    story.append(Paragraph("Chaque produit est répertorié avec ses conditions tarifaires et ses règles de gestion :", body_style))
    story.append(Paragraph("• <b>Code SKU & Code-barres :</b> Identifiant unique pour le scan rapide à la caisse.", bullet_style))
    story.append(Paragraph("• <b>Prix en Franc CFA :</b> Prix d'achat HT (calcul de marge) et Prix de vente TTC affiché au client.", bullet_style))
    story.append(Paragraph("• <b>Régime TVA :</b> 18% (Taux standard UEMOA) ou 0% (Articles exonérés).", bullet_style))
    story.append(Paragraph("• <b>Seuil d'Alerte :</b> Niveau minimum déclenchant automatiquement l'alerte sur le tableau de bord.", bullet_style))
    story.append(Spacer(1, 3))

    cat_path = "/home/user/NEXORA/docs/screenshots/04_catalog.png"
    if os.path.exists(cat_path):
        story.append(Image(cat_path, width=500, height=185))
        story.append(Paragraph("Figure 3.0 — Liste et configuration des fiches articles avec prix en FCFA, TVA et alertes", fig_style))

    story.append(Paragraph("5. Gestion des Dépôts, Stocks & Inventaires", h1_style))
    story.append(Paragraph("NEXORA garantit une traçabilité totale : chaque mouvement d'inventaire est signé par son auteur.", body_style))
    story.append(Paragraph("• <b>Sorties Ventes POS :</b> Décrémentation automatique en temps réel à chaque ticket validé.", bullet_style))
    story.append(Paragraph("• <b>Entrées Réceptions Fournisseurs :</b> Incrémentation immédiate dès validation de la commande.", bullet_style))
    story.append(Paragraph("• <b>Ajustements d'Inventaire :</b> Régularisation des écarts physiques justifiés (casse, vol, perte).", bullet_style))
    story.append(Spacer(1, 3))

    inv_path = "/home/user/NEXORA/docs/screenshots/05_inventory.png"
    if os.path.exists(inv_path):
        story.append(Image(inv_path, width=500, height=185))
        story.append(Paragraph("Figure 4.0 — Journal des mouvements d'entrepôt (Ventes, Réceptions d'achats, Transferts)", fig_style))

    story.append(PageBreak())

    # ==================== PAGE 4 : CLÔTURE DE CAISSE (RAPPORT Z) & RAPPORTS TVA ====================
    story.append(Paragraph("6. Clôture Quotidienne de Caisse (Rapport Z Officiel)", h1_style))
    story.append(Paragraph("À la fin de chaque journée ou lors d'un changement d'équipe, le caissier réalise sa clôture de caisse :", body_style))
    story.append(Paragraph("1. Cliquer sur le bouton rouge <b>« Clôturer Caisse (Z) »</b> dans le POS.", bullet_style))
    story.append(Paragraph("2. <b>Comptage physique des espèces :</b> Renseigner les billets et pièces réels dans le formulaire de coupures.", bullet_style))
    story.append(Paragraph("3. <b>Rapprochement électronique :</b> Confirmer les totaux reçus via Orange Money, Moov Money et Wave.", bullet_style))
    story.append(Paragraph("4. <b>Contrôle des Écarts :</b> Le système compare le théorique et le physique et certifie l'écart (Surplus ou Déficit).", bullet_style))
    story.append(Paragraph("5. <b>Édition du Rapport Z :</b> Impression du ticket légal officiel scellé non modifiable.", bullet_style))
    story.append(Spacer(1, 3))

    clot_path = "/home/user/NEXORA/docs/screenshots/06_closure_z.png"
    if os.path.exists(clot_path):
        story.append(Image(clot_path, width=500, height=185))
        story.append(Paragraph("Figure 5.0 — Procédure de clôture quotidienne : Recomptage des espèces, rapprochement Mobile Money et Rapport Z", fig_style))

    story.append(Paragraph("7. Rapports Financiers & Déclaration de TVA (18% UEMOA)", h1_style))
    story.append(Paragraph("Le module Rapports consolide tous les états nécessaires à la comptabilité et à la télédéclaration fiscale :", body_style))
    story.append(Paragraph("• <b>Chiffre d'Affaires Brut & Net :</b> États consolidés quotidiens, mensuels et trimestriels.", bullet_style))
    story.append(Paragraph("• <b>Déclaration TVA 18% :</b> Suivi séparé de la TVA collectée (ventes) et TVA déductible (achats).", bullet_style))
    story.append(Paragraph("• <b>Marges & Bénéfice Net :</b> Rentabilité réelle dégagée par rayon pour guider les décisions de la direction.", bullet_style))
    story.append(Spacer(1, 3))

    rep_path = "/home/user/NEXORA/docs/screenshots/03_reports.png"
    if os.path.exists(rep_path):
        story.append(Image(rep_path, width=500, height=185))
        story.append(Paragraph("Figure 6.0 — États Financiers Consolidés et Déclaration de TVA (18% UEMOA) dans le module Rapports", fig_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF complet de 4 pages généré avec succès !")

if __name__ == "__main__":
    build_pdf("/home/user/NEXORA/GUIDE_UTILISATEUR.pdf")
    build_pdf("/home/user/NEXORA/frontend/public/GUIDE_UTILISATEUR.pdf")
