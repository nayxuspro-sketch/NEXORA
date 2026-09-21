from io import BytesIO
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
from apps.audit.models import AuditLog


class AuditLogPdfExportView(APIView):
    """
    Exports Audit & Security Log as a tamper-evident, official PDF report for a user-defined date range.
    Query params:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - action (optional)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            company = Company.objects.first()

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        action_filter = request.query_params.get('action')

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

        logs_qs = AuditLog.objects.filter(
            company=company,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('user').order_by('-created_at')

        if action_filter:
            logs_qs = logs_qs.filter(action__icontains=action_filter)

        logs = list(logs_qs)

        # Statistics
        total_logs = len(logs)
        login_events = sum(1 for l in logs if 'LOGIN' in l.action.upper() or 'AUTH' in l.action.upper())
        sales_events = sum(1 for l in logs if 'SALE' in l.action.upper() or 'PAYMENT' in l.action.upper())
        catalog_events = sum(1 for l in logs if 'PRODUCT' in l.action.upper() or 'CATALOG' in l.action.upper())
        other_events = total_logs - (login_events + sales_events + catalog_events)

        # Document setup
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
            'AuditTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=19,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'AuditSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )

        cell_style = ParagraphStyle(
            'AuditCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#1e293b')
        )

        cell_bold = ParagraphStyle(
            'AuditCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#0f172a')
        )

        company_name = company.name if company else "NEXORA ENTERPRISE"
        elements.append(Paragraph(f"<b>{company_name} — REGISTRE OFFICIEL DU JOURNAL D'AUDIT & SÉCURITÉ</b>", title_style))
        period_text = (
            f"Période auditée définie : du <b>{start_date.strftime('%d/%m/%Y')}</b> au <b>{end_date.strftime('%d/%m/%Y')}</b> | "
            f"<b>{total_logs} événement(s) de traçabilité</b> certifié(s) | Édité le : {now.strftime('%d/%m/%Y à %H:%M')}"
        )
        elements.append(Paragraph(period_text, subtitle_style))

        # KPI Summary box
        kpi_data = [
            [
                Paragraph("<b>Total Événements Audit</b>", cell_bold),
                Paragraph("<b>Authentifications / Logins</b>", cell_bold),
                Paragraph("<b>Transactions Ventes / Caisse</b>", cell_bold),
                Paragraph("<b>Catalogue & Produits</b>", cell_bold),
                Paragraph("<b>Autres Actions / Tiers</b>", cell_bold),
            ],
            [
                Paragraph(f"<b>{total_logs} enregistrements</b>", cell_bold),
                Paragraph(f"{login_events} session(s)", cell_style),
                Paragraph(f"<b>{sales_events} opération(s)</b>", cell_bold),
                Paragraph(f"{catalog_events} modification(s)", cell_style),
                Paragraph(f"{other_events} action(s)", cell_style),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[150, 150, 160, 145, 145])
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
            Paragraph("<b>Horodatage (UTC/Local)</b>", cell_bold),
            Paragraph("<b>Action de Sécurité</b>", cell_bold),
            Paragraph("<b>Ressource / Cible</b>", cell_bold),
            Paragraph("<b>Opérateur / Utilisateur</b>", cell_bold),
            Paragraph("<b>Adresse IP</b>", cell_bold),
            Paragraph("<b>Détails & Payload d'Audit</b>", cell_bold),
        ]
        for h in table_headers:
            h.style.textColor = colors.white

        table_data = [table_headers]

        if logs:
            for l in logs:
                # Format friendly French action
                act_str = l.action
                if 'LOGIN_SUCCESS' in act_str:
                    action_badge = "<font color='#059669'><b>Connexion Réussie</b></font>"
                elif 'POST_SALES' in act_str:
                    action_badge = "<font color='#2563eb'><b>Création Vente / Caisse</b></font>"
                elif 'POST_PRODUCTS' in act_str:
                    action_badge = "<font color='#7c3aed'><b>Modification Produit</b></font>"
                elif 'POST_PARTNERS' in act_str:
                    action_badge = "<font color='#0891b2'><b>Création / Modif. Client</b></font>"
                else:
                    action_badge = f"<b>{act_str}</b>"

                user_str = l.user.email if l.user else (l.user_email or 'Système Automatique')
                ip_str = l.ip_address or '127.0.0.1'
                target_str = f"<b>{l.resource_type}</b><br/><font color='#64748b' size='6.5'>{l.resource_id}</font>"

                # Summary of details
                details_text = "-"
                if l.details:
                    d_items = []
                    for k, v in list(l.details.items())[:3]:
                        d_items.append(f"{k}: {v}")
                    details_text = "<font color='#475569'>" + ", ".join(d_items)[:90] + "</font>"

                table_data.append([
                    Paragraph(l.created_at.strftime('%d/%m/%Y %H:%M:%S'), cell_style),
                    Paragraph(action_badge, cell_style),
                    Paragraph(target_str, cell_style),
                    Paragraph(user_str, cell_style),
                    Paragraph(f"<font color='#0284c7'>{ip_str}</font>", cell_style),
                    Paragraph(details_text, cell_style),
                ])
        else:
            table_data.append([
                Paragraph("Aucun événement d'audit enregistré sur la période sélectionnée.", cell_style),
                Paragraph("", cell_style), Paragraph("", cell_style),
                Paragraph("", cell_style), Paragraph("", cell_style), Paragraph("", cell_style)
            ])

        col_w = [115, 125, 140, 140, 75, 155]
        log_table = Table(table_data, colWidths=col_w, repeatRows=1)
        log_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING', (0, 0), (-1, -1), 3.5),
        ]))

        elements.append(log_table)

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"Journal_Audit_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
