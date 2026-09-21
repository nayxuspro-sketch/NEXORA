from io import BytesIO
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from apps.companies.models import Company
from apps.inventory.models import Store, StockLevel, StockMovement
from apps.catalog.models import Product


class StockLevelPdfExportView(APIView):
    """
    Exports Stock Levels as a professional PDF report for a given period or at a specific date.
    Query params:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - store_id (optional)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            company = Company.objects.first()

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        store_id = request.query_params.get('store_id')

        # Date parsing
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
                end_date = timezone.make_aware(datetime.combine(end_date.date(), datetime.max.time()))
            except Exception:
                pass

        if not end_date:
            end_date = now
        if not start_date:
            start_date = end_date - timezone.timedelta(days=30)

        # Stores filter
        stores_qs = Store.objects.filter(company=company)
        if store_id:
            stores_qs = stores_qs.filter(id=store_id)

        # Products
        products = Product.objects.filter(company=company, is_active=True).order_by('name')

        # Compute stock per product and store
        report_rows = []
        total_valuation_cost = Decimal('0.00')
        total_valuation_retail = Decimal('0.00')
        total_units = Decimal('0.00')

        for store in stores_qs:
            for prod in products:
                # 1. Base current stock
                current_stock_obj = StockLevel.objects.filter(store=store, product=prod).first()
                current_qty = current_stock_obj.quantity if current_stock_obj else Decimal('0.00')

                # 2. Movements after end_date to rewind to end_date
                moves_after_end = StockMovement.objects.filter(
                    store=store,
                    product=prod,
                    created_at__gt=end_date
                )
                net_after_end = sum([m.quantity for m in moves_after_end], Decimal('0.00'))
                qty_at_end = current_qty - net_after_end

                # 3. Movements during period [start_date, end_date]
                period_moves = StockMovement.objects.filter(
                    store=store,
                    product=prod,
                    created_at__gte=start_date,
                    created_at__lte=end_date
                )
                net_period_change = sum([m.quantity for m in period_moves], Decimal('0.00'))
                qty_at_start = qty_at_end - net_period_change

                # In/Out within period
                total_in = sum([m.quantity for m in period_moves if m.quantity > 0], Decimal('0.00'))
                total_out = abs(sum([m.quantity for m in period_moves if m.quantity < 0], Decimal('0.00')))

                cost_val = qty_at_end * prod.cost_price
                retail_val = qty_at_end * prod.selling_price

                total_valuation_cost += cost_val
                total_valuation_retail += retail_val
                total_units += qty_at_end

                report_rows.append({
                    'store': store.name,
                    'name': prod.name,
                    'sku': prod.sku,
                    'unit': prod.unit.symbol if prod.unit else 'pcs',
                    'start_qty': qty_at_start,
                    'in_qty': total_in,
                    'out_qty': total_out,
                    'end_qty': qty_at_end,
                    'unit_cost': prod.cost_price,
                    'unit_price': prod.selling_price,
                    'cost_val': cost_val,
                })

        # Generate PDF with ReportLab
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#475569'),
            spaceAfter=14
        )

        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1e293b')
        )

        cell_bold = ParagraphStyle(
            'CellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#0f172a')
        )

        # Header Title
        company_name = company.name if company else "NEXORA ENTERPRISE"
        elements.append(Paragraph(f"<b>{company_name} — ÉTAT ET NIVEAU DES STOCKS PAR PÉRIODE</b>", title_style))
        period_text = f"Période analysée : du <b>{start_date.strftime('%d/%m/%Y')}</b> au <b>{end_date.strftime('%d/%m/%Y')}</b> | Devise : <b>FCFA (XOF)</b> | Édité le : {now.strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(period_text, subtitle_style))

        # KPI Summary box Table
        kpi_data = [
            [
                Paragraph("<b>Total Références</b>", cell_bold),
                Paragraph("<b>Unités en Stock Fin</b>", cell_bold),
                Paragraph("<b>Valorisation Coût d'Achat</b>", cell_bold),
                Paragraph("<b>Valorisation Prix Vente</b>", cell_bold),
            ],
            [
                Paragraph(f"{len(report_rows)} articles", cell_style),
                Paragraph(f"{total_units:,.2f}".replace(',', ' '), cell_bold),
                Paragraph(f"{total_valuation_cost:,.0f} FCFA".replace(',', ' '), cell_bold),
                Paragraph(f"{total_valuation_retail:,.0f} FCFA".replace(',', ' '), cell_bold),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[180, 180, 200, 200])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # Data Table
        table_headers = [
            Paragraph("<b>Magasin / Dépôt</b>", cell_bold),
            Paragraph("<b>Article & SKU</b>", cell_bold),
            Paragraph("<b>Stock Début</b>", cell_bold),
            Paragraph("<b>Entrées (+)</b>", cell_bold),
            Paragraph("<b>Sorties (-)</b>", cell_bold),
            Paragraph("<b>Stock Fin</b>", cell_bold),
            Paragraph("<b>Coût Unit. HT</b>", cell_bold),
            Paragraph("<b>Prix Vente TTC</b>", cell_bold),
            Paragraph("<b>Valorisation Coût</b>", cell_bold),
        ]

        table_data = [table_headers]

        for r in report_rows:
            p_desc = f"{r['name']}<br/><font color='#64748b' size='6.5'>SKU: {r['sku']}</font>"
            table_data.append([
                Paragraph(r['store'], cell_style),
                Paragraph(p_desc, cell_style),
                Paragraph(f"{r['start_qty']:,.0f}".replace(',', ' '), cell_style),
                Paragraph(f"+{r['in_qty']:,.0f}".replace(',', ' ') if r['in_qty'] > 0 else "-", cell_style),
                Paragraph(f"-{r['out_qty']:,.0f}".replace(',', ' ') if r['out_qty'] > 0 else "-", cell_style),
                Paragraph(f"<b>{r['end_qty']:,.0f} {r['unit']}</b>".replace(',', ' '), cell_bold),
                Paragraph(f"{r['unit_cost']:,.0f}".replace(',', ' '), cell_style),
                Paragraph(f"{r['unit_price']:,.0f}".replace(',', ' '), cell_style),
                Paragraph(f"<b>{r['cost_val']:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
            ])

        col_widths = [105, 170, 65, 65, 65, 75, 75, 75, 95]
        stock_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        stock_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING', (0, 0), (-1, -1), 4.5),
        ]))

        # Fix header text colors inside paragraphs
        for i in range(len(table_headers)):
            table_headers[i].style.textColor = colors.white

        elements.append(stock_table)

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"Etat_Stocks_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class StockMovementPdfExportView(APIView):
    """
    Exports Stock Movements Audit Log as a professional PDF report for a given period.
    Query params:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - store_id (optional)
    - movement_type (optional)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            company = Company.objects.first()

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        store_id = request.query_params.get('store_id')
        m_type = request.query_params.get('movement_type')

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
                end_date = timezone.make_aware(datetime.combine(end_date.date(), datetime.max.time()))
            except Exception:
                pass

        if not end_date:
            end_date = now
        if not start_date:
            start_date = end_date - timezone.timedelta(days=30)

        movements_qs = StockMovement.objects.filter(
            company=company,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('product', 'store', 'user').order_by('-created_at')

        if store_id:
            movements_qs = movements_qs.filter(store_id=store_id)
        if m_type:
            movements_qs = movements_qs.filter(movement_type=m_type)

        movements = list(movements_qs)

        # Totals
        total_in = sum([m.quantity for m in movements if m.quantity > 0], Decimal('0.00'))
        total_out = abs(sum([m.quantity for m in movements if m.quantity < 0], Decimal('0.00')))
        net_flow = total_in - total_out

        # Generate PDF with ReportLab
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'MoveTitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=19,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'MoveSubtitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )

        cell_style = ParagraphStyle(
            'MoveCellStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#1e293b')
        )

        cell_bold = ParagraphStyle(
            'MoveCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#0f172a')
        )

        company_name = company.name if company else "NEXORA ENTERPRISE"
        elements.append(Paragraph(f"<b>{company_name} — GRAND LIVRE DES MOUVEMENTS DE STOCKS</b>", title_style))
        period_text = f"Période auditée : du <b>{start_date.strftime('%d/%m/%Y')}</b> au <b>{end_date.strftime('%d/%m/%Y')}</b> | {len(movements)} écriture(s) trouvée(s) | Édité le : {now.strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(period_text, subtitle_style))

        # KPI Summary box
        kpi_data = [
            [
                Paragraph("<b>Total Écritures</b>", cell_bold),
                Paragraph("<b>Total Entrées (+)</b>", cell_bold),
                Paragraph("<b>Total Sorties (-)</b>", cell_bold),
                Paragraph("<b>Variation Nette Globale</b>", cell_bold),
            ],
            [
                Paragraph(f"{len(movements)} mouvements", cell_style),
                Paragraph(f"+{total_in:,.0f} unités".replace(',', ' '), cell_bold),
                Paragraph(f"-{total_out:,.0f} unités".replace(',', ' '), cell_bold),
                Paragraph(f"{net_flow:+,.0f} unités".replace(',', ' '), cell_bold),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[180, 180, 200, 200])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 12))

        # Table Headers
        table_headers = [
            Paragraph("<b>Date & Heure</b>", cell_bold),
            Paragraph("<b>Type de Flux</b>", cell_bold),
            Paragraph("<b>Article & SKU</b>", cell_bold),
            Paragraph("<b>Dépôt / Magasin</b>", cell_bold),
            Paragraph("<b>Quantité</b>", cell_bold),
            Paragraph("<b>Avant → Après</b>", cell_bold),
            Paragraph("<b>Référence & Motif</b>", cell_bold),
            Paragraph("<b>Opérateur</b>", cell_bold),
        ]

        table_data = [table_headers]

        for m in movements:
            is_pos = m.quantity > 0
            qty_color = '#059669' if is_pos else '#dc2626'
            qty_str = f"<font color='{qty_color}'><b>{m.quantity:+,.0f}</b></font>".replace(',', ' ')

            p_desc = f"{m.product.name}<br/><font color='#64748b' size='6.5'>SKU: {m.product.sku}</font>"
            ref_desc = f"<b>{m.reference or 'Sans réf.'}</b><br/><font color='#64748b' size='6.5'>{m.reason or ''}</font>"
            user_str = m.user.email if m.user else 'Système Automatique'

            table_data.append([
                Paragraph(m.created_at.strftime('%d/%m/%Y %H:%M'), cell_style),
                Paragraph(f"<b>{m.get_movement_type_display()}</b>", cell_style),
                Paragraph(p_desc, cell_style),
                Paragraph(m.store.name, cell_style),
                Paragraph(qty_str, cell_style),
                Paragraph(f"{m.quantity_before:,.0f} → <b>{m.quantity_after:,.0f}</b>".replace(',', ' '), cell_style),
                Paragraph(ref_desc, cell_style),
                Paragraph(user_str, cell_style),
            ])

        col_widths = [95, 95, 175, 115, 60, 85, 125, 90]
        moves_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        moves_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))

        for i in range(len(table_headers)):
            table_headers[i].style.textColor = colors.white

        elements.append(moves_table)

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"Grand_Livre_Mouvements_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
