from apps.common.renderers import PassthroughBinaryRenderer
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from apps.companies.models import Company
from apps.sales.models import Sale, SaleStatus
from apps.inventory.models import Store
from apps.common.pdf_header import get_store_logo_flowable, create_header_with_logo


class BilanBySellerPdfView(APIView):
    renderer_classes = [PassthroughBinaryRenderer]
    """
    Exports a comparative sales statement grouped by seller:
    one summary row per seller (validated sales count, revenue, collected,
    outstanding, average basket, gross margin, revenue share) with ranking.

    Query params:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            company = Company.objects.first()

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        days_param = request.query_params.get('days')
        days = int(days_param) if days_param and days_param.isdigit() else 30

        now = timezone.now()
        start_date = None
        end_date = None

        if start_date_str:
            try:
                parsed = datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date = timezone.make_aware(datetime.combine(parsed.date(), datetime.min.time()))
            except Exception:
                pass

        if end_date_str:
            try:
                parsed = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = timezone.make_aware(datetime.combine(parsed.date(), datetime.max.time()))
            except Exception:
                pass

        if not end_date:
            end_date = now + timezone.timedelta(days=1)
        else:
            end_date = max(end_date, now + timezone.timedelta(hours=4))

        if not start_date:
            start_date = now - timezone.timedelta(days=days)

        sales_qs = Sale.objects.all()
        if company:
            sales_qs = sales_qs.filter(company=company)

        sales_qs = sales_qs.filter(
            status=SaleStatus.COMPLETED,
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        sales = list(sales_qs.select_related('seller').prefetch_related('items__product').order_by('-created_at'))

        sellers = {}
        grand_revenue = Decimal('0.00')
        grand_paid = Decimal('0.00')
        grand_cogs = Decimal('0.00')

        for s in sales:
            if s.seller:
                key = str(s.seller.id)
                name = s.seller.get_full_name() or s.seller.email
                email = s.seller.email
                role = s.seller.get_role_display() if hasattr(s.seller, 'get_role_display') else 'Vendeur'
            else:
                key = '__unassigned__'
                name = 'Vendeur non attribué'
                email = '—'
                role = 'Système'

            if key not in sellers:
                sellers[key] = {
                    'name': name,
                    'email': email,
                    'role': role,
                    'count': 0,
                    'revenue': Decimal('0.00'),
                    'paid': Decimal('0.00'),
                    'qty': Decimal('0.00'),
                    'cogs': Decimal('0.00'),
                }

            row = sellers[key]
            row['count'] += 1
            row['revenue'] += s.total_amount or Decimal('0.00')
            row['paid'] += s.paid_amount or Decimal('0.00')

            sale_cogs = Decimal('0.00')
            for item in s.items.all():
                cost_p = item.product.cost_price if item.product else Decimal('0.00')
                row['qty'] += item.quantity
                sale_cogs += item.quantity * cost_p
            row['cogs'] += sale_cogs

            grand_revenue += s.total_amount or Decimal('0.00')
            grand_paid += s.paid_amount or Decimal('0.00')
            grand_cogs += sale_cogs

        rows = sorted(sellers.values(), key=lambda r: r['revenue'], reverse=True)
        for r in rows:
            r['outstanding'] = r['revenue'] - r['paid']
            r['margin'] = r['revenue'] - r['cogs']
            r['avg_basket'] = (r['revenue'] / Decimal(str(r['count']))).quantize(Decimal('1.00')) if r['count'] else Decimal('0.00')
            r['share'] = (r['revenue'] / grand_revenue * Decimal('100')).quantize(Decimal('0.1')) if grand_revenue > Decimal('0.00') else Decimal('0.0')

        total_count = len(sales)
        total_margin = grand_revenue - grand_cogs
        total_outstanding = grand_revenue - grand_paid
        global_avg = (grand_revenue / Decimal(str(total_count))).quantize(Decimal('1.00')) if total_count else Decimal('0.00')

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

        title_style = ParagraphStyle(
            'BilanTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=19,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=3
        )

        subtitle_style = ParagraphStyle(
            'BilanSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )

        section_heading = ParagraphStyle(
            'BilanSection',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#1e3a8a'),
            spaceBefore=8,
            spaceAfter=6
        )

        table_header_style = ParagraphStyle(
            'BilanTh',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#ffffff')
        )

        cell_style = ParagraphStyle(
            'BilanTd',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.8,
            leading=10,
            textColor=colors.HexColor('#0f172a')
        )

        cell_right = ParagraphStyle('BilanTdRight', parent=cell_style, alignment=2)

        cell_bold = ParagraphStyle(
            'BilanTdBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.8,
            leading=10,
            textColor=colors.HexColor('#0f172a')
        )

        cell_bold_right = ParagraphStyle('BilanTdBoldRight', parent=cell_bold, alignment=2)

        kpi_label_style = ParagraphStyle(
            'BilanKpiLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#0284c7')
        )

        analysis_body = ParagraphStyle(
            'BilanAnalysis',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )

        company_name = company.name if company else "NEXORA ENTERPRISE"

        store_logo_str = ""
        if company:
            store = Store.objects.filter(company=company).first()
            if store:
                store_logo_str = getattr(store, 'logo', '')

        logo_flowable = get_store_logo_flowable(store_logo_str, max_width=80, max_height=45)

        title_p = Paragraph(f"<b>{company_name} — BILAN DES VENTES PAR VENDEUR</b>", title_style)
        subtitle_p = Paragraph(
            f"Période du <b>{start_date.strftime('%d/%m/%Y')}</b> au <b>{end_date.strftime('%d/%m/%Y')}</b> | "
            f"Ventes validées uniquement | Devise : <b>FCFA (XOF)</b> | Généré le {now.strftime('%d/%m/%Y à %H:%M')}",
            subtitle_style
        )

        elements.extend(create_header_with_logo(title_p, subtitle_p, logo_flowable, total_width=539))
        elements.append(Spacer(1, 8))

        kpi_table_data = [
            [
                Paragraph("<b>Chiffre d'Affaires Total</b>", kpi_label_style),
                Paragraph("<b>Ventes Validées</b>", kpi_label_style),
                Paragraph("<b>Vendeurs Actifs</b>", kpi_label_style),
                Paragraph("<b>Panier Moyen Global</b>", kpi_label_style),
                Paragraph("<b>Marge Brute Totale</b>", kpi_label_style),
            ],
            [
                Paragraph(f"<b>{grand_revenue:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
                Paragraph(f"{total_count} vente(s)", cell_style),
                Paragraph(f"{len(rows)} vendeur(s)", cell_style),
                Paragraph(f"<b>{global_avg:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
                Paragraph(f"<b>{total_margin:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
            ]
        ]
        kpi_table = Table(kpi_table_data, colWidths=[112, 100, 95, 115, 117])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("<b>Tableau Récapitulatif de Performance par Vendeur :</b>", section_heading))

        headers = [
            Paragraph("<b>Rang</b>", table_header_style),
            Paragraph("<b>Vendeur</b>", table_header_style),
            Paragraph("<b>Ventes</b>", table_header_style),
            Paragraph("<b>Articles</b>", table_header_style),
            Paragraph("<b>CA Réalisé</b>", table_header_style),
            Paragraph("<b>Réglé</b>", table_header_style),
            Paragraph("<b>Reste à Encaisser</b>", table_header_style),
            Paragraph("<b>Panier Moyen</b>", table_header_style),
            Paragraph("<b>Marge Brute</b>", table_header_style),
            Paragraph("<b>Part CA</b>", table_header_style),
        ]

        table_data = [headers]

        if rows:
            for rank, r in enumerate(rows, start=1):
                seller_cell = [
                    Paragraph(f"<b>{r['name']}</b>", cell_bold),
                    Paragraph(f"{r['email']} — {r['role']}", ParagraphStyle(
                        'SellerMeta', parent=cell_style, fontSize=6.5, textColor=colors.HexColor('#64748b')
                    )),
                ]
                out_color = '#b91c1c' if r['outstanding'] > Decimal('0.00') else '#047857'
                table_data.append([
                    Paragraph(f"<b>#{rank}</b>", cell_bold),
                    seller_cell,
                    Paragraph(str(r['count']), cell_right),
                    Paragraph(f"{r['qty']:,.0f}".replace(',', ' '), cell_right),
                    Paragraph(f"<b>{r['revenue']:,.0f}</b>".replace(',', ' '), cell_bold_right),
                    Paragraph(f"{r['paid']:,.0f}".replace(',', ' '), cell_right),
                    Paragraph(f"<font color='{out_color}'><b>{r['outstanding']:,.0f}</b></font>".replace(',', ' '), cell_right),
                    Paragraph(f"{r['avg_basket']:,.0f}".replace(',', ' '), cell_right),
                    Paragraph(f"{r['margin']:,.0f}".replace(',', ' '), cell_bold_right),
                    Paragraph(f"<b>{r['share']}%</b>", cell_right),
                ])

            table_data.append([
                Paragraph("", cell_style),
                Paragraph("<b>TOTAL ENTREPRISE</b>", cell_bold),
                Paragraph(f"<b>{total_count}</b>", cell_bold_right),
                Paragraph(f"<b>{sum(r['qty'] for r in rows):,.0f}</b>".replace(',', ' '), cell_bold_right),
                Paragraph(f"<b>{grand_revenue:,.0f}</b>".replace(',', ' '), cell_bold_right),
                Paragraph(f"<b>{grand_paid:,.0f}</b>".replace(',', ' '), cell_bold_right),
                Paragraph(f"<b>{total_outstanding:,.0f}</b>".replace(',', ' '), cell_bold_right),
                Paragraph(f"<b>{global_avg:,.0f}</b>".replace(',', ' '), cell_bold_right),
                Paragraph(f"<b>{total_margin:,.0f}</b>".replace(',', ' '), cell_bold_right),
                Paragraph("<b>100%</b>", cell_bold_right),
            ])
        else:
            table_data.append([
                Paragraph("<b>Aucune vente validée sur la période sélectionnée.</b>", cell_style),
                Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style),
                Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style),
                Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style),
            ])

        col_w = [26, 112, 34, 38, 66, 58, 58, 52, 55, 40]
        bilan_table = Table(table_data, colWidths=col_w, repeatRows=1)
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('TOPPADDING', (0, 0), (-1, 0), 5.5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5.5),
            ('TOPPADDING', (0, 1), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 3.5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3.5),
        ]
        if rows:
            style_cmds.append(('BACKGROUND', (0, len(table_data) - 1), (-1, len(table_data) - 1), colors.HexColor('#e0f2fe')))
            style_cmds.append(('LINEABOVE', (0, len(table_data) - 1), (-1, len(table_data) - 1), 1, colors.HexColor('#0284c7')))
        bilan_table.setStyle(TableStyle(style_cmds))
        elements.append(bilan_table)

        if rows:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("<b>Lecture du Bilan :</b>", section_heading))

            top = rows[0]
            top_share = top['share']
            elements.append(Paragraph(
                f"• <b>Meilleur vendeur :</b> <b>{top['name']}</b> domine la période avec "
                f"<b>{top['revenue']:,.0f} FCFA</b> de chiffre d'affaires ({top_share}% des recettes), "
                f"réalisés sur {top['count']} vente(s) à un panier moyen de {top['avg_basket']:,.0f} FCFA.".replace(',', ' '),
                analysis_body
            ))

            unpaid_rows = [r for r in rows if r['outstanding'] > Decimal('0.00')]
            if unpaid_rows:
                worst = max(unpaid_rows, key=lambda r: r['outstanding'])
                elements.append(Paragraph(
                    f"• <b>Suivi des créances :</b> {total_outstanding:,.0f} FCFA restent à encaisser sur l'ensemble des vendeurs. "
                    f"Le plus gros encours est porté par <b>{worst['name']}</b> ({worst['outstanding']:,.0f} FCFA) : "
                    f"une relance de recouvrement est recommandée.".replace(',', ' '),
                    analysis_body
                ))
            else:
                elements.append(Paragraph(
                    "• <b>Suivi des créances :</b> toutes les ventes validées de la période ont été intégralement encaissées. Aucun encours à relancer.",
                    analysis_body
                ))

            margin_pct = (total_margin / grand_revenue * Decimal('100')).quantize(Decimal('0.1')) if grand_revenue > Decimal('0.00') else Decimal('0.0')
            elements.append(Paragraph(
                f"• <b>Rentabilité :</b> la marge brute cumulée s'élève à {total_margin:,.0f} FCFA, soit {margin_pct}% du CA. "
                f"Les ventes à faible marge ou concédées en remise doivent être arbitrées par la direction commerciale.".replace(',', ' '),
                analysis_body
            ))

            if len(rows) > 1:
                weakest = rows[-1]
                if weakest['revenue'] < grand_revenue * Decimal('0.1'):
                    elements.append(Paragraph(
                        f"• <b>Dispersion des performances :</b> <b>{weakest['name']}</b> ne contribue qu'à hauteur de "
                        f"{weakest['share']}% du CA. Un accompagnement commercial ciblé (formation, argumentaire, objectifs) "
                        f"est conseillé pour rééquilibrer l'effort de vente.".replace(',', ' '),
                        analysis_body
                    ))

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        import unicodedata
        company_ascii = unicodedata.normalize('NFKD', company_name or 'NEXORA').encode('ASCII', 'ignore').decode('utf-8')
        company_clean = company_ascii.replace(' ', '_').replace('/', '_')
        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"Bilan_Par_Vendeur_{company_clean}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
