import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
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
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 800, "NEXORA Enterprise ERP & POS — Guide Officiel d'Utilisation")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 794, 540, 794)
        
        # Footer
        page_text = f"Page {self._pageNumber} sur {page_count}"
        self.drawRightString(540, 36, page_text)
        self.drawString(54, 36, "Confidential & Proprietary • Édition UEMOA (FCFA)")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 540, 48)
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    box_text_style = ParagraphStyle(
        'BoxText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e3a8a')
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("NEXORA ERP & POS", title_style))
    story.append(Paragraph("Manuel & Guide d'Utilisation Officiel — Édition UEMOA (FCFA)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284c7'), spaceAfter=14))

    # Introduction Box
    intro_data = [[
        Paragraph("<b>À propos de ce document :</b> Ce manuel est destiné aux administrateurs, comptables, gestionnaires de stock et caissiers exploitant la plateforme commerciale <b>NEXORA</b>. Conforme aux normes commerciales et fiscales en vigueur dans l'espace UEMOA (Burkina Faso, Sénégal, Côte d'Ivoire, Mali, etc.). Devise par défaut : <b>Franc CFA (XOF / FCFA)</b>.", box_text_style)
    ]]
    intro_table = Table(intro_data, colWidths=[486])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bfdbfe')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 14))

    # Section 1 : Accès et Authentification
    story.append(Paragraph("1. Accès au Système & Identifiants par Défaut", h1_style))
    story.append(Paragraph("La plateforme s'utilise via un navigateur moderne (Chrome, Edge, Firefox, Safari) :", body_style))
    story.append(Paragraph("• <b>Interface Web & Point de Vente :</b> <font color='#0284c7'>http://localhost:3000</font> (ou IP réseau local)", bullet_style))
    story.append(Paragraph("• <b>Administration Centrale & API :</b> <font color='#0284c7'>http://localhost:8000/admin/</font>", bullet_style))
    story.append(Spacer(1, 6))

    users_data = [
        [Paragraph("<b>Profil / Rôle</b>", body_style), Paragraph("<b>Identifiant</b>", body_style), Paragraph("<b>Mot de passe</b>", body_style), Paragraph("<b>Droits d'accès</b>", body_style)],
        [Paragraph("Directeur / Admin", body_style), Paragraph("admin", body_style), Paragraph("Admin123456!", body_style), Paragraph("Accès total (Ventes, Stocks, Achats, Clôtures, Rapports, Paramètres)", body_style)],
        [Paragraph("Caissier / Vendeur", body_style), Paragraph("cashier", body_style), Paragraph("Cashier123!", body_style), Paragraph("Accès dédié Caisse POS, encaissements et clôture de sa session", body_style)],
    ]
    t_users = Table(users_data, colWidths=[100, 75, 95, 216])
    t_users.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_users)
    story.append(Spacer(1, 14))

    # Section 2 : Point de Vente
    story.append(Paragraph("2. Utilisation de la Caisse Enregistreuse (POS)", h1_style))
    story.append(Paragraph("Le module POS permet de fluidifier les encaissements en magasin ou supermarché :", body_style))
    story.append(Paragraph("1. <b>Ouvrir la session de caisse :</b> Cliquez sur <i>« Ouvrir Caisse »</i> et indiquez le fond de caisse initial.", bullet_style))
    story.append(Paragraph("2. <b>Ajouter des produits :</b> Scannez le code-barres avec une douchette, sélectionnez directement dans la grille tactile, ou saisissez le nom dans la barre de recherche.", bullet_style))
    story.append(Paragraph("3. <b>Ajuster quantités et remises :</b> Utilisez les touches + / - ou entrez la quantité au clavier numérique.", bullet_style))
    story.append(Paragraph("4. <b>Règlement (<font color='#0284c7'>F8</font>) :</b> Sélectionnez le mode de règlement (Espèces, Orange Money, Moov Money, Wave, Carte bancaire). En espèces, entrez la somme remise pour afficher le calcul exact du rendu de monnaie en FCFA.", bullet_style))
    story.append(Paragraph("5. <b>Impression du ticket :</b> Le ticket de caisse thermique (format 80mm ou 58mm) est imprimé automatiquement et le stock est mis à jour.", bullet_style))
    story.append(Spacer(1, 6))

    # Raccourcis Box
    shortcut_data = [
        [Paragraph("<b>Raccourci</b>", body_style), Paragraph("<b>Action associée</b>", body_style)],
        [Paragraph("<b>F2</b>", body_style), Paragraph("Curseur instantané dans la barre de recherche produit", body_style)],
        [Paragraph("<b>F4</b>", body_style), Paragraph("Sélectionner ou changer de client (Comptoir / Compte pro)", body_style)],
        [Paragraph("<b>F8</b>", body_style), Paragraph("Ouvrir la fenêtre d'encaissement et de choix de paiement", body_style)],
        [Paragraph("<b>F10</b>", body_style), Paragraph("Mettre la vente en attente (servir le client suivant)", body_style)],
        [Paragraph("<b>ESC</b>", body_style), Paragraph("Annuler l'opération en cours ou vider le panier", body_style)],
    ]
    t_short = Table(shortcut_data, colWidths=[100, 386])
    t_short.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_short)
    story.append(Spacer(1, 14))

    # Section 3 : Stocks
    story.append(Paragraph("3. Gestion des Stocks et Réapprovisionnements", h1_style))
    story.append(Paragraph("• <b>Fiche Article :</b> Chaque article dispose d'une référence SKU, d'un prix de vente en FCFA, d'un prix d'achat, d'un taux de TVA (0% exonéré ou 18% standard UEMOA) et d'un seuil critique d'alerte.", bullet_style))
    story.append(Paragraph("• <b>Mouvements Automatisés :</b> Chaque vente au comptoir décrémente instantanément le stock de l'entrepôt principal. Chaque réception de commande fournisseur l'incrémente.", bullet_style))
    story.append(Paragraph("• <b>Inventaires & Régularisations :</b> Permet de comparer le stock physique réel avec le stock théorique et de justifier les écarts constatés.", bullet_style))
    story.append(Spacer(1, 14))

    # Section 4 : Clôture de Caisse (Rapport Z)
    story.append(Paragraph("4. Clôture Quotidienne & Rapport Z", h1_style))
    story.append(Paragraph("En fin de service, chaque caissier doit impérativement exécuter la procédure de fermeture :", body_style))
    story.append(Paragraph("1. Cliquer sur <i>« Clôturer la Session »</i>.", bullet_style))
    story.append(Paragraph("2. Compter physiquement les billets et pièces dans le tiroir-caisse et renseigner le total espèces.", bullet_style))
    story.append(Paragraph("3. Valider les soldes reçus par paiements mobiles (Orange Money, Wave, etc.).", bullet_style))
    story.append(Paragraph("4. Le système calcule immédiatement l'écart (Excédent ou Déficit de caisse) et génère le <b>Rapport Z</b> officiel non modifiable.", bullet_style))
    story.append(Spacer(1, 14))

    # Section 5 : Rapports Financiers & TVA
    story.append(Paragraph("5. Rapports Financiers & Déclarations Fiscales", h1_style))
    story.append(Paragraph("Le tableau de bord décisionnel consolide les indicateurs en temps réel :", body_style))
    story.append(Paragraph("• <b>Chiffre d'Affaires Brut & Net :</b> Synthèse quotidienne, mensuelle et annuelle en Franc CFA.", bullet_style))
    story.append(Paragraph("• <b>État de TVA (18%) :</b> Récapitulatif ventilé de la TVA collectée sur les ventes et déductible sur les achats, prêt pour la télédéclaration fiscale.", bullet_style))
    story.append(Paragraph("• <b>Marges & Rentabilité :</b> Analyse des marges bénéficiaires par rayon et identification des produits à forte valeur ajoutée.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF généré avec succès : {filename}")

if __name__ == "__main__":
    out_dir = "/home/user/NEXORA"
    build_pdf(os.path.join(out_dir, "GUIDE_UTILISATEUR.pdf"))
    build_pdf(os.path.join(out_dir, "frontend/public/GUIDE_UTILISATEUR.pdf"))
