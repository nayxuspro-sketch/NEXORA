from io import BytesIO
from decimal import Decimal
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from apps.companies.models import Company
from apps.catalog.models import Product, Category
from apps.inventory.models import StockLevel


class ProductCatalogPdfExportView(APIView):
    """
    Exports the Product Catalog as a professional PDF report filtered by STATUS:
    - ALL: Tous les produits
    - ACTIVE: Produits Actifs uniquement (disponibles à la vente)
    - INACTIVE: Produits Inactifs uniquement (archivés / suspendus)
    - OUT_OF_STOCK: Produits en Rupture de stock (stock <= 0)
    - LOW_STOCK: Produits sous le Seuil d'Alerte (0 < stock <= seuil)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            company = Company.objects.first()

        status_filter = request.query_params.get('status', 'ALL').upper()
        category_id = request.query_params.get('category_id')
        now = timezone.now()

        products_qs = Product.objects.filter(company=company).select_related('category', 'unit').order_by('name')

        if category_id:
            products_qs = products_qs.filter(category_id=category_id)

        # Pre-compute stock levels per product
        stock_levels_qs = StockLevel.objects.filter(company=company)
        stock_by_prod = {}
        for sl in stock_levels_qs:
            stock_by_prod[sl.product_id] = stock_by_prod.get(sl.product_id, Decimal('0.00')) + sl.quantity

        filtered_products = []
        for p in products_qs:
            current_stock = stock_by_prod.get(p.id, Decimal('0.00'))
            is_active = p.is_active

            # Apply status filter
            if status_filter == 'ACTIVE' and not is_active:
                continue
            elif status_filter == 'INACTIVE' and is_active:
                continue
            elif status_filter == 'OUT_OF_STOCK' and current_stock > Decimal('0.00'):
                continue
            elif status_filter == 'LOW_STOCK':
                if current_stock <= Decimal('0.00') or current_stock > p.alert_threshold:
                    continue

            filtered_products.append({
                'product': p,
                'stock': current_stock,
            })

        # Statistics
        total_items = len(filtered_products)
        active_count = sum(1 for item in filtered_products if item['product'].is_active)
        inactive_count = total_items - active_count
        total_stock_units = sum(item['stock'] for item in filtered_products)
        total_val_cost = sum(item['stock'] * item['product'].cost_price for item in filtered_products)
        total_val_retail = sum(item['stock'] * item['product'].selling_price for item in filtered_products)

        # Status label in French
        status_titles = {
            'ALL': 'Tous les Statuts (Actifs et Inactifs)',
            'ACTIVE': 'Articles Actifs Uniquement (En vente)',
            'INACTIVE': 'Articles Inactifs Uniquement (Archivés)',
            'OUT_OF_STOCK': 'Articles en Rupture de Stock (Stock ≤ 0)',
            'LOW_STOCK': "Articles sous le Seuil d'Alerte (Stock Critique)",
        }
        current_status_label = status_titles.get(status_filter, status_filter)

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
            'CatTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=19,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'CatSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )

        cell_style = ParagraphStyle(
            'CatCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#1e293b')
        )

        cell_bold = ParagraphStyle(
            'CatCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#0f172a')
        )

        company_name = company.name if company else "NEXORA ENTERPRISE"
        elements.append(Paragraph(f"<b>{company_name} — CATALOGUE DES PRODUITS PAR STATUT</b>", title_style))
        elements.append(Paragraph(
            f"Filtre appliqué : <b>{current_status_label}</b> | {total_items} référence(s) répertoriée(s) | Devise : <b>FCFA (XOF)</b> | Édité le : {now.strftime('%d/%m/%Y à %H:%M')}",
            subtitle_style
        ))

        # KPI Box
        kpi_data = [
            [
                Paragraph("<b>Total Articles</b>", cell_bold),
                Paragraph("<b>Actifs / Inactifs</b>", cell_bold),
                Paragraph("<b>Unités en Stock</b>", cell_bold),
                Paragraph("<b>Valorisation Coût Achat</b>", cell_bold),
                Paragraph("<b>Valorisation Vente TTC</b>", cell_bold),
            ],
            [
                Paragraph(f"<b>{total_items} référence(s)</b>", cell_bold),
                Paragraph(f"{active_count} actif(s) / {inactive_count} inactif(s)", cell_style),
                Paragraph(f"<b>{total_stock_units:,.0f} pcs</b>".replace(',', ' '), cell_bold),
                Paragraph(f"<b>{total_val_cost:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
                Paragraph(f"<b>{total_val_retail:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[140, 150, 140, 175, 175])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 10))

        # Table Headers
        table_headers = [
            Paragraph("<b>Désignation de l'Article</b>", cell_bold),
            Paragraph("<b>SKU / Réf.</b>", cell_bold),
            Paragraph("<b>Code-barres / EAN</b>", cell_bold),
            Paragraph("<b>Famille / Catégorie</b>", cell_bold),
            Paragraph("<b>Prix Achat HT</b>", cell_bold),
            Paragraph("<b>Prix Vente TTC</b>", cell_bold),
            Paragraph("<b>Marge / Unité</b>", cell_bold),
            Paragraph("<b>Stock Dispo</b>", cell_bold),
            Paragraph("<b>Seuil Min</b>", cell_bold),
            Paragraph("<b>Statut</b>", cell_bold),
        ]
        for h in table_headers:
            h.style.textColor = colors.white

        table_data = [table_headers]

        for item in filtered_products:
            p = item['product']
            stock = item['stock']
            cat_name = p.category.name if p.category else 'Non classé'
            unit_sym = p.unit.symbol if p.unit else 'pcs'
            barcode_str = p.barcode if p.barcode else '-'

            unit_margin = p.selling_price - p.cost_price
            status_text = 'ACTIF' if p.is_active else 'INACTIF'
            status_color = '#059669' if p.is_active else '#dc2626'

            # Stock color
            if stock <= Decimal('0.00'):
                stock_color = '#dc2626'
                stock_label = f"<b>{stock:,.0f} (Rupture)</b>"
            elif stock <= p.alert_threshold:
                stock_color = '#d97706'
                stock_label = f"<b>{stock:,.0f} (Alerte)</b>"
            else:
                stock_color = '#059669'
                stock_label = f"<b>{stock:,.0f} {unit_sym}</b>"

            table_data.append([
                Paragraph(f"<b>{p.name}</b>", cell_bold),
                Paragraph(f"<font color='#0284c7'><b>{p.sku}</b></font>", cell_style),
                Paragraph(barcode_str, cell_style),
                Paragraph(cat_name, cell_style),
                Paragraph(f"{p.cost_price:,.0f} FCFA".replace(',', ' '), cell_style),
                Paragraph(f"<b>{p.selling_price:,.0f} FCFA</b>".replace(',', ' '), cell_bold),
                Paragraph(f"{unit_margin:,.0f}".replace(',', ' '), cell_style),
                Paragraph(f"<font color='{stock_color}'>{stock_label}</font>".replace(',', ' '), cell_style),
                Paragraph(f"{p.alert_threshold:,.0f}".replace(',', ' '), cell_style),
                Paragraph(f"<font color='{status_color}'><b>{status_text}</b></font>", cell_style),
            ])

        col_w = [150, 75, 80, 105, 75, 80, 65, 75, 45, 50]
        cat_table = Table(table_data, colWidths=col_w, repeatRows=1)
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('ALIGN', (4, 0), (8, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING', (0, 0), (-1, -1), 3.5),
        ]))

        elements.append(cat_table)

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        status_slug = status_filter.lower()
        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"Catalogue_Produits_{status_slug}_{now.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
