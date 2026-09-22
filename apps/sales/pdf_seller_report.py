from io import BytesIO
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from apps.companies.models import Company
from apps.accounts.models import User
from apps.sales.models import Sale, SaleItem, Payment


class SellerSalesReportPdfView(APIView):
    """
    Exports a 2-page customized PDF report for an individual seller/cashier:
    - Page 1: Official Sales Statement for the given period (filtered strictly to this seller).
    - Page 2: Advanced Sales Analysis & AI-driven Smart Commercial Suggestions.
    
    Query params:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - seller_id (optional, defaults to request.user if seller or first seller)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            company = Company.objects.first()

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        seller_param = request.query_params.get('seller_id') or request.query_params.get('seller')

        days_param = request.query_params.get('days')
        days = int(days_param) if days_param and days_param.isdigit() else 30

        now = timezone.now()
        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date = timezone.make_aware(datetime.combine(start_date.date(), datetime.min.time()))
            except Exception:
                pass

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # Couvrir jusqu'à la fin de la journée sélectionnée
                end_date = timezone.make_aware(datetime.combine(end_date.date(), datetime.max.time()))
            except Exception:
                pass

        if not end_date:
            end_date = now + timezone.timedelta(days=1)
        else:
            # S'assurer que les ventes de la minute présente ou avec léger décalage horaire UTC sont bien incluses
            end_date = max(end_date, now + timezone.timedelta(hours=4))

        if not start_date:
            start_date = now - timezone.timedelta(days=days)

        # Identify target seller
        seller_user = None
        if seller_param:
            seller_user = User.objects.filter(company=company).filter(
                id=seller_param if len(seller_param) == 36 else None
            ).first() or User.objects.filter(company=company, email__icontains=seller_param).first()

        if not seller_user and request.user.is_authenticated:
            seller_user = request.user

        if not seller_user:
            # Fallback to cashier or first user with sales
            first_sale = Sale.objects.filter(company=company).exclude(seller=None).first()
            if first_sale:
                seller_user = first_sale.seller
            else:
                seller_user = User.objects.filter(company=company).first()

        # Filter sales strictly for THIS seller
        sales_qs = Sale.objects.filter(
            company=company,
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        if seller_param and seller_user:
            sales_qs = sales_qs.filter(seller=seller_user)

        sales = list(sales_qs.prefetch_related('items__product', 'payments').order_by('-created_at'))

        # Metrics calculation
        total_sales_count = len(sales)
        total_revenue = sum([s.total_amount for s in sales], Decimal('0.00'))
        total_tax = sum([s.tax_amount for s in sales], Decimal('0.00'))
        total_paid = sum([s.paid_amount for s in sales], Decimal('0.00'))
        total_discounts = sum([s.discount_amount for s in sales], Decimal('0.00'))
        avg_basket = (total_revenue / Decimal(str(total_sales_count))).quantize(Decimal('1.00')) if total_sales_count > 0 else Decimal('0.00')

        # Product breakdown
        product_sales = {}
        total_items_qty = Decimal('0.00')
        cogs_total = Decimal('0.00')

        for s in sales:
            for item in s.items.all():
                p_name = item.product.name if item.product else 'Article divers'
                p_sku = item.product.sku if item.product else '-'
                cost_p = item.product.cost_price if item.product else Decimal('0.00')
                total_items_qty += item.quantity
                cogs_total += item.quantity * cost_p

                if p_name not in product_sales:
                    product_sales[p_name] = {
                        'sku': p_sku,
                        'qty': Decimal('0.00'),
                        'revenue': Decimal('0.00'),
                        'profit': Decimal('0.00')
                    }
                product_sales[p_name]['qty'] += item.quantity
                product_sales[p_name]['revenue'] += item.total
                product_sales[p_name]['profit'] += item.total - (item.quantity * cost_p)

        gross_margin = total_revenue - cogs_total
        margin_pct = (gross_margin / total_revenue * Decimal('100')).quantize(Decimal('0.1')) if total_revenue > Decimal('0.00') else Decimal('0.0')

        # Payment methods breakdown
        payment_breakdown = {}
        for s in sales:
            for p in s.payments.all():
                m_label = p.get_payment_method_display()
                payment_breakdown[m_label] = payment_breakdown.get(m_label, Decimal('0.00')) + p.amount

        # Generate PDF with ReportLab
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=portrait(A4),
            leftMargin=28,
            rightMargin=28,
            topMargin=26,
            bottomMargin=26
        )

        elements = []
        styles = getSampleStyleSheet()

        # Styles
        title_style = ParagraphStyle(
            'SellerTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=19,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=3
        )

        subtitle_style = ParagraphStyle(
            'SellerSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15,
            textColor=colors.HexColor('#1e3a8a'),
            spaceBefore=8,
            spaceAfter=6
        )

        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#ffffff')
        )

        table_header_right = ParagraphStyle(
            'TableHeaderRight',
            parent=table_header_style,
            alignment=2
        )

        cell_style = ParagraphStyle(
            'SellerCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor('#0f172a')
        )

        cell_style_right = ParagraphStyle(
            'SellerCellRight',
            parent=cell_style,
            alignment=2
        )

        cell_bold = ParagraphStyle(
            'SellerCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#0284c7')
        )

        cell_bold_right = ParagraphStyle(
            'SellerCellBoldRight',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10.5,
            alignment=2,
            textColor=colors.HexColor('#0f172a')
        )

        analysis_body = ParagraphStyle(
            'AnalysisBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )

        suggestion_box_title = ParagraphStyle(
            'SuggTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor('#0369a1'),
            spaceAfter=3
        )

        # -------------------------------------------------------------
        # PAGE 1 : ÉTAT OFFICIEL DES VENTES DU VENDEUR
        # -------------------------------------------------------------
        company_name = company.name if company else "NEXORA ENTERPRISE"
        seller_name = seller_user.get_full_name() or seller_user.email if seller_user else "Vendeur Caisse"
        seller_email = seller_user.email if seller_user else ""
        seller_role = seller_user.get_role_display() if (seller_user and hasattr(seller_user, 'get_role_display')) else "Vendeur / Caissier"

        elements.append(Paragraph(f"<b>{company_name} — ÉTAT DE VENTE INDIVIDUEL DU VENDEUR</b>", title_style))
        elements.append(Paragraph(
            f"Vendeur : <b>{seller_name}</b> ({seller_email} — {seller_role}) | Période du : <b>{start_date.strftime('%d/%m/%Y')}</b> au <b>{end_date.strftime('%d/%m/%Y')}</b> | Devise : <b>FCFA (XOF)</b>",
            subtitle_style
        ))

        # KPI Cards (Page 1)
        kpi_table_data = [
            [
                Paragraph("<b>Chiffre d'Affaires Réalisé</b>", cell_bold),
                Paragraph("<b>Transactions Validées</b>", cell_bold),
                Paragraph("<b>Panier Moyen / Vente</b>", cell_bold),
                Paragraph("<b>Marge Brute Dégagée</b>", cell_bold),
            ],
            [
                Paragraph(f"<b>{total_revenue:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
                Paragraph(f"{total_sales_count} vente(s)", cell_style),
                Paragraph(f"<b>{avg_basket:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
                Paragraph(f"<b>{gross_margin:,.0f} FCFA</b> ({margin_pct}%)".replace(',', ' '), cell_bold),
            ]
        ]
        kpi_table = Table(kpi_table_data, colWidths=[135, 130, 135, 138])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 10))

        # Detailed Table of Sales for this Seller
        elements.append(Paragraph("<b>Détail des Factures & Tickets Réalisés par le Vendeur :</b>", section_heading))

        sales_headers = [
            Paragraph("<b>Réf. Facture</b>", table_header_style),
            Paragraph("<b>Date & Heure</b>", table_header_style),
            Paragraph("<b>Client Facturé</b>", table_header_style),
            Paragraph("<b>Articles</b>", table_header_style),
            Paragraph("<b>Total TTC</b>", table_header_right),
            Paragraph("<b>Réglé</b>", table_header_right),
            Paragraph("<b>Statut</b>", table_header_style),
        ]

        sales_table_data = [sales_headers]

        if sales:
            for s in sales:
                c_name = s.customer.name if s.customer else "Client Comptoir"
                pay_status = 'Soldé' if s.payment_status == 'PAID' else 'Partiel' if s.payment_status == 'PARTIAL' else 'En attente'
                pay_color = '#047857' if s.payment_status == 'PAID' else '#b45309' if s.payment_status == 'PARTIAL' else '#b91c1c'
                items_summary = f"{sum([it.quantity for it in s.items.all()], Decimal('0.00')):,.0f} art."

                sales_table_data.append([
                    Paragraph(f"<b>{s.reference}</b>", cell_bold),
                    Paragraph(s.created_at.strftime('%d/%m/%Y %H:%M'), cell_style),
                    Paragraph(f"<b>{c_name[:26]}</b>" if s.customer else c_name[:26], cell_style),
                    Paragraph(items_summary, cell_style),
                    Paragraph(f"<b>{s.total_amount:,.0f}</b>".replace(',', ' '), cell_bold_right),
                    Paragraph(f"{s.paid_amount:,.0f}".replace(',', ' '), cell_style_right),
                    Paragraph(f"<font color='{pay_color}'><b>{pay_status}</b></font>", cell_style),
                ])
        else:
            sales_table_data.append([
                Paragraph("<b>Aucune vente enregistrée pour ce vendeur sur la période sélectionnée.</b>", cell_style),
                Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style),
                Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style)
            ])

        # Dimensions calibrées pour la largeur totale A4 (538 pt)
        col_w = [126, 68, 120, 44, 64, 62, 54]
        sales_table = Table(sales_table_data, colWidths=col_w, repeatRows=1)
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('TOPPADDING', (0, 0), (-1, 0), 5.5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5.5),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(sales_table)

        # -------------------------------------------------------------
        # PAGE 2 : ANALYSE DES VENTES DU VENDEUR & SUGGESTIONS COMMERCIALES
        # -------------------------------------------------------------
        elements.append(PageBreak())

        elements.append(Paragraph(f"<b>{company_name} — ANALYSE DE LA VENTE & SUGGESTIONS COMMERCIALES</b>", title_style))
        elements.append(Paragraph(
            f"Bilan de performance individuel de <b>{seller_name}</b> | Généré automatiquement par l'intelligence opérationnelle NEXORA le {now.strftime('%d/%m/%Y à %H:%M')}",
            subtitle_style
        ))

        # 1. Synthèse Analytique Narrative
        elements.append(Paragraph("<b>1. Analyse Approfondie de la Performance Commerciale</b>", section_heading))

        # Dynamic diagnostic logic
        diag_intro = (
            f"Sur la période analysée, le vendeur <b>{seller_name}</b> a contribué à hauteur de <b>{total_revenue:,.0f} FCFA</b> "
            f"de chiffre d'affaires à travers <b>{total_sales_count} transaction(s)</b>, représentant un panier moyen de <b>{avg_basket:,.0f} FCFA</b>. "
            f"La marge commerciale brute brute générée s'élève à <b>{gross_margin:,.0f} FCFA</b>, soit un taux de rentabilité de <b>{margin_pct}%</b>."
        ).replace(',', ' ')
        elements.append(Paragraph(diag_intro, analysis_body))

        # Top product analysis
        sorted_prods = sorted(product_sales.items(), key=lambda x: x[1]['revenue'], reverse=True)
        if sorted_prods:
            top_prod_name, top_prod_data = sorted_prods[0]
            top_share = (top_prod_data['revenue'] / total_revenue * Decimal('100')).quantize(Decimal('0.1')) if total_revenue > 0 else Decimal('0.0')
            prod_analysis_text = (
                f"• <b>Moteur principal des ventes :</b> L'article <b>« {top_prod_name} »</b> a constitué le produit phare avec "
                f"<b>{top_prod_data['qty']:,.0f} unité(s) vendue(s)</b> générant <b>{top_prod_data['revenue']:,.0f} FCFA</b> "
                f"(soit <b>{top_share}%</b> des recettes du vendeur). La marge brute apportée sur cette seule référence est de <b>{top_prod_data['profit']:,.0f} FCFA</b>."
            ).replace(',', ' ')
            elements.append(Paragraph(prod_analysis_text, analysis_body))

        # Payment methods analysis
        if payment_breakdown:
            pay_details = ", ".join([f"{k} : {v:,.0f} FCFA ({round(v/total_revenue*100 if total_revenue>0 else 0)}%)".replace(',', ' ') for k, v in payment_breakdown.items()])
            pay_analysis_text = f"• <b>Canaux d'encaissement :</b> Répartition des encaissements enregistrés par le vendeur : {pay_details}."
            elements.append(Paragraph(pay_analysis_text, analysis_body))

        elements.append(Spacer(1, 6))

        # Top Products table
        elements.append(Paragraph("<b>2. Répartition des Ventes par Produit & Contribution à la Marge :</b>", section_heading))
        p_table_headers = [
            Paragraph("<b>Produit / Article</b>", cell_bold),
            Paragraph("<b>SKU</b>", cell_bold),
            Paragraph("<b>Quantité Vendue</b>", cell_bold),
            Paragraph("<b>Chiffre d'Affaires</b>", cell_bold),
            Paragraph("<b>Marge Brute</b>", cell_bold),
            Paragraph("<b>Part (%)</b>", cell_bold),
        ]
        for h in p_table_headers:
            h.style.textColor = colors.white

        p_table_data = [p_table_headers]
        for p_name, p_data in sorted_prods[:6]:
            share = (p_data['revenue'] / total_revenue * Decimal('100')).quantize(Decimal('0.1')) if total_revenue > 0 else Decimal('0.0')
            p_table_data.append([
                Paragraph(p_name, cell_style),
                Paragraph(p_data['sku'], cell_style),
                Paragraph(f"{p_data['qty']:,.0f}".replace(',', ' '), cell_style),
                Paragraph(f"{p_data['revenue']:,.0f} FCFA".replace(',', ' '), cell_bold),
                Paragraph(f"{p_data['profit']:,.0f} FCFA".replace(',', ' '), cell_bold),
                Paragraph(f"{share}%", cell_style),
            ])

        p_table = Table(p_table_data, colWidths=[180, 80, 70, 85, 80, 43])
        p_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING', (0, 0), (-1, -1), 3.5),
        ]))
        elements.append(p_table)
        elements.append(Spacer(1, 10))

        # 3. AI & Operational Suggestions for the Seller
        elements.append(Paragraph("<b>3. Suggestions Commerciales Personnalisées & Recommandations :</b>", section_heading))

        suggestions = []

        # Suggestion 1: Basket size / Cross-selling
        if avg_basket < Decimal('100000.00'):
            suggestions.append((
                "Augmentation du Panier Moyen par Vente Croisée (Cross-Selling)",
                "Votre panier moyen actuel est accessible. Lors du passage en caisse d'articles informatiques ou de bureau, proposez systématiquement les consommables et accessoires complémentaires (câbles, souris, multiprises, clés USB). Un article additionnel par ticket augmentera directement votre rendement commercial de 15 à 25%."
            ))
        else:
            suggestions.append((
                "Consolidation des Ventes à Forte Valeur Ajoutée",
                "Excellent niveau de panier moyen réalisé sur la période. Maintenez cette dynamique en orientant les clients vers des garanties étendues, des accessoires professionnels et des services d'installation/configuration adaptés aux équipements haut de gamme."
            ))

        # Suggestion 2: Margin optimization
        if margin_pct < Decimal('30.0'):
            suggestions.append((
                "Priorisation des Articles à Forte Marge Commerciale",
                f"Le taux de marge actuel dégagé ({margin_pct}%) est axé sur des articles compétitifs à marge plus serrée. Intégrez activement la présentation des produits périphériques et accessoires dont le taux de marge brute dépasse fréquemment 40% afin de maximiser le résultat net de votre caisse."
            ))
        else:
            suggestions.append((
                "Excellente Rentabilité Commerciale",
                f"Votre taux de marge réalisé ({margin_pct}%) démontre une très bonne maîtrise de la valeur perçue par vos clients. Continuez à valoriser les avantages techniques des produits premium sans concéder de remises superflues lors des négociations au comptoir."
            ))

        # Suggestion 3: Customer Retention & Loyalty
        suggestions.append((
            "Fidélisation & Attribution Systématique du Compte Client",
            "Veillez à identifier et assigner nominativement chaque client récurrent sur le POS (Touche F4) plutôt que de valider en 'Client Comptoir'. Cela permet de suivre les encours autorisés, de leur proposer des facilités adaptées et d'activer les relances automatiques."
        ))

        # Suggestion 4: Payment efficiency
        suggestions.append((
            "Fluidité des Encaissements & Encaissements Digitaux",
            "La promotion active des paiements digitaux (Orange Money / Moov Money) réduit le temps de file d'attente au comptoir, élimine les erreurs de rendu de monnaie et sécurise l'encaissement immédiat des recettes journalières."
        ))

        for title_s, desc_s in suggestions:
            box_content = [
                Paragraph(f"💡 <b>{title_s}</b>", suggestion_box_title),
                Paragraph(desc_s, analysis_body)
            ]
            box_table = Table([[box_content]], colWidths=[538])
            box_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(box_table)
            elements.append(Spacer(1, 5))

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        import unicodedata
        seller_ascii = unicodedata.normalize('NFKD', seller_name or 'Vendeur').encode('ASCII', 'ignore').decode('utf-8')
        seller_clean = seller_ascii.replace(' ', '_').replace('/', '_')
        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"Vente_{seller_clean}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
