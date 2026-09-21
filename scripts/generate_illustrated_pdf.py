import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, HRFlowable
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
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(50, 802, "NEXORA ENTERPRISE ERP & POS — Manuel d'Utilisation Officiel Illustré")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(50, 796, 545, 796)
        
        # Footer
        page_text = f"Page {self._pageNumber} sur {page_count}"
        self.drawRightString(545, 32, page_text)
        self.setFont("Helvetica", 8)
        self.drawString(50, 32, "Édition Afrique de l'Ouest (FCFA / XOF) • Conforme UEMOA & OHADA")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(50, 42, 545, 42)
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=48,
        bottomMargin=48
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
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
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
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
        leading=11,
        textColor=colors.HexColor('#475569'),
        alignment=1, # Centered
        spaceBefore=4,
        spaceAfter=10
    )

    story = []

    # Title
    story.append(Paragraph("NEXORA ERP & Point de Vente (POS)", title_style))
    story.append(Paragraph("Manuel d'Utilisation Officiel Illustré — Édition UEMOA (FCFA)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=10))

    # Intro box
    intro_p = Paragraph("<b>Guide Pratique :</b> Ce manuel illustré détaille l'utilisation opérationnelle du logiciel commercial NEXORA, configuré avec les devises en <b>Franc CFA (FCFA)</b>, la taxe <b>TVA standard à 18%</b> et la gestion des paiements <b>Mobile Money</b> (Orange Money, Moov Money, Wave).", body_style)
    intro_table = Table([[intro_p]], colWidths=[499])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#bfdbfe')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 10))

    # Section 1 : Accès & Connexion
    story.append(Paragraph("1. Accès au Logiciel & Identifiants Prédéfinis", h1_style))
    story.append(Paragraph("• <b>Adresse Interface Web & Caisse :</b> <font color='#0284c7'>http://localhost:3000</font> (ou IP réseau de l'ordinateur caisse)", bullet_style))
    story.append(Paragraph("• <b>Portail d'Administration Technique :</b> <font color='#0284c7'>http://localhost:8008/admin/</font>", bullet_style))
    story.append(Spacer(1, 4))

    users_data = [
        [Paragraph("<b>Rôle Utilisateur</b>", body_style), Paragraph("<b>Identifiant</b>", body_style), Paragraph("<b>Mot de passe</b>", body_style), Paragraph("<b>Autorisations</b>", body_style)],
        [Paragraph("Directeur / Gérant", body_style), Paragraph("admin", body_style), Paragraph("Admin123456!", body_style), Paragraph("Accès complet : Tableaux de bord, Stocks, Achats, Clôtures Z, Rapports financiers et TVA", body_style)],
        [Paragraph("Caissier / Vendeur", body_style), Paragraph("cashier", body_style), Paragraph("Cashier123!", body_style), Paragraph("Accès exclusif : Écran Caisse POS tactile, encaissements et clôture de sa vacation", body_style)],
    ]
    t_users = Table(users_data, colWidths=[105, 65, 85, 244])
    t_users.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_users)
    story.append(Spacer(1, 10))

    # Section 2 : Dashboard avec capture d'écran
    story.append(Paragraph("2. Le Tableau de Bord Stratégique en Temps Réel", h1_style))
    story.append(Paragraph("Le tableau de bord permet à la direction de surveiller en un coup d'œil la rentabilité et le volume d'affaires :", body_style))
    story.append(Paragraph("• <b>Chiffre d'Affaires consolidé (FCFA) :</b> Ventes totales nettes réalisées sur les 30 derniers jours.", bullet_style))
    story.append(Paragraph("• <b>Marge Brute Réalisée :</b> Bénéfice commercial après déduction automatique des coûts d'achat.", bullet_style))
    story.append(Paragraph("• <b>Alertes de Rupture :</b> Détection immédiate des articles sous le stock minimum de sécurité.", bullet_style))
    story.append(Spacer(1, 4))

    # Capture 1
    dash_img_path = "/home/user/NEXORA/docs/screenshots/01_dashboard.png"
    if os.path.exists(dash_img_path):
        story.append(Image(dash_img_path, width=490, height=210))
        story.append(Paragraph("Figure 1.0 — Vue d'ensemble du Tableau de bord NEXORA avec indicateurs en FCFA et alertes", fig_style))

    story.append(PageBreak())

    # Section 3 : POS avec capture d'écran
    story.append(Paragraph("3. Le Point de Vente (POS / Caisse Enregistreuse)", h1_style))
    story.append(Paragraph("L'écran de caisse tactile est conçu pour le débit rapide de clients en boutique ou supermarché :", body_style))
    story.append(Paragraph("1. <b>Sélection des articles :</b> Scannez avec la douchette de codes-barres, cliquez sur les tuiles tactiles ou appuyez sur <b>F2</b> pour chercher par référence.", bullet_style))
    story.append(Paragraph("2. <b>Validation du Panier :</b> Modification instantanée des quantités (+ / -) et application de remises.", bullet_style))
    story.append(Paragraph("3. <b>Encaissement Multi-Moyens :</b> Espèces avec rendu de monnaie automatique en FCFA, Orange Money, Moov Money, Wave ou Carte Bancaire.", bullet_style))
    story.append(Paragraph("4. <b>Impression du Ticket (F8) :</b> Génération du ticket thermique 80mm conforme et déstockage immédiat.", bullet_style))
    story.append(Spacer(1, 4))

    # Capture 2
    pos_img_path = "/home/user/NEXORA/docs/screenshots/02_pos.png"
    if os.path.exists(pos_img_path):
        story.append(Image(pos_img_path, width=490, height=210))
        story.append(Paragraph("Figure 2.0 — Interface de la Caisse Enregistreuse POS (Sélection tactile et Encaissement Mobile Money)", fig_style))

    # Tableau raccourcis
    short_data = [
        [Paragraph("<b>Raccourci</b>", body_style), Paragraph("<b>Action Caissier</b>", body_style), Paragraph("<b>Raccourci</b>", body_style), Paragraph("<b>Action Caissier</b>", body_style)],
        [Paragraph("<b>F2</b>", body_style), Paragraph("Recherche rapide d'article", body_style), Paragraph("<b>F8</b>", body_style), Paragraph("Fenêtre d'encaissement / Valider", body_style)],
        [Paragraph("<b>F4</b>", body_style), Paragraph("Sélectionner ou changer de client", body_style), Paragraph("<b>F10</b>", body_style), Paragraph("Mettre la vente en attente", body_style)],
    ]
    t_short = Table(short_data, colWidths=[65, 184, 65, 185])
    t_short.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_short)
    story.append(Spacer(1, 10))

    # Section 4 : Clôture & Rapports avec capture
    story.append(Paragraph("4. Clôture de Caisse (Rapport Z) & Rapports de TVA", h1_style))
    story.append(Paragraph("• <b>Clôture Quotidienne (Z) :</b> En fin de journée, le caissier compte le liquide du tiroir et valide les soldes Mobile Money. Le système calcule les écarts éventuels et édite le Rapport Z officiel.", bullet_style))
    story.append(Paragraph("• <b>Déclaration Fiscale TVA 18% :</b> Le module Rapports ventile automatiquement la TVA collectée sur les ventes et la TVA déductible sur les achats, conforme pour la déclaration fiscale.", bullet_style))
    story.append(Spacer(1, 4))

    # Capture 3
    rep_img_path = "/home/user/NEXORA/docs/screenshots/03_reports.png"
    if os.path.exists(rep_img_path):
        story.append(Image(rep_img_path, width=490, height=200))
        story.append(Paragraph("Figure 3.0 — États Financiers Consolidés et Déclaration de TVA (18% UEMOA) dans le module Rapports", fig_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF illustré généré avec succès !")

if __name__ == "__main__":
    build_pdf("/home/user/NEXORA/GUIDE_UTILISATEUR.pdf")
    build_pdf("/home/user/NEXORA/frontend/public/GUIDE_UTILISATEUR.pdf")
