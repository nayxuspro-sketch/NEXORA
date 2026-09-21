import hashlib
import hmac
from datetime import datetime
from io import BytesIO

from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse

from rest_framework import serializers, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from apps.companies.models import Company, StoreLicense
from apps.inventory.models import Store


def generate_cryptographic_license_key(store, plan_type, expires_at_str, max_registers):
    """
    Generates a tamper-evident HMAC-SHA256 signature and license string.
    """
    secret = getattr(settings, 'SECRET_KEY', 'nexora-secret-salt-2026')
    raw_payload = f"NEXORA-LIC|{store.id}|{store.code}|{plan_type}|{expires_at_str}|{max_registers}"
    signature = hmac.new(secret.encode('utf-8'), raw_payload.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    
    # Human-readable formatted key: NX-XXXX-XXXX-XXXX-XXXX
    chunk1 = signature[0:4]
    chunk2 = signature[4:8]
    chunk3 = signature[8:12]
    chunk4 = signature[12:16]
    formatted_key = f"NX-{store.code[:4].upper()}-{chunk1}-{chunk2}-{chunk3}-{chunk4}"
    
    return formatted_key, signature


class StoreLicenseSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_code = serializers.CharField(source='store.code', read_only=True)
    is_valid = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()

    class Meta:
        model = StoreLicense
        fields = [
            'id', 'company', 'store', 'store_name', 'store_code',
            'license_key', 'plan_type', 'max_registers', 'issued_to_name',
            'valid_from', 'expires_at', 'signature_hash', 'is_revoked',
            'is_valid', 'remaining_days', 'created_at'
        ]
        read_only_fields = ['id', 'company', 'license_key', 'signature_hash', 'created_at']

    def get_is_valid(self, obj):
        if obj.is_revoked:
            return False
        return obj.expires_at >= timezone.now().date()

    def get_remaining_days(self, obj):
        delta = (obj.expires_at - timezone.now().date()).days
        return max(0, delta)

    def create(self, validated_data):
        store = validated_data['store']
        company = store.company
        plan = validated_data.get('plan_type', 'PRO')
        expires_at = validated_data['expires_at']
        max_regs = validated_data.get('max_registers', 3)

        formatted_key, sig = generate_cryptographic_license_key(store, plan, str(expires_at), max_regs)
        
        license_obj = StoreLicense.objects.create(
            company=company,
            store=store,
            license_key=formatted_key,
            plan_type=plan,
            max_registers=max_regs,
            issued_to_name=validated_data.get('issued_to_name', store.name),
            valid_from=validated_data.get('valid_from', timezone.now().date()),
            expires_at=expires_at,
            signature_hash=sig,
            is_revoked=False
        )
        return license_obj


class StoreLicenseViewSet(viewsets.ModelViewSet):
    """
    CRUD management of Store software licenses.
    """
    permission_classes = [AllowAny]
    queryset = StoreLicense.objects.select_related('store').all().order_by('-created_at')
    serializer_class = StoreLicenseSerializer
    search_fields = ['license_key', 'store__name', 'issued_to_name']


class StoreLicenseCertificatePdfExportView(APIView):
    """
    Generates and downloads the official Certificate of Authenticity & Software License (PDF).
    """
    permission_classes = [AllowAny]

    def get(self, request, license_id):
        lic = StoreLicense.objects.filter(id=license_id).select_related('store', 'company').first()
        if not lic:
            return Response({'error': 'Licence introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        company = lic.company or Company.objects.first()
        store = lic.store

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'LicTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0f172a'),
            alignment=1,
            spaceAfter=4
        )

        sub_style = ParagraphStyle(
            'LicSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            alignment=1,
            spaceAfter=15
        )

        label_style = ParagraphStyle(
            'LicLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )

        val_style = ParagraphStyle(
            'LicVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0f172a')
        )

        key_style = ParagraphStyle(
            'LicKey',
            parent=styles['Normal'],
            fontName='Courier-Bold',
            fontSize=14,
            leading=17,
            textColor=colors.HexColor('#1d4ed8'),
            alignment=1
        )

        # Header
        elements.append(Paragraph(f"<b>NEXORA ENTERPRISE ERP — BURKINA FASO</b>", title_style))
        elements.append(Paragraph("<b>CERTIFICAT OFFICIEL DE LICENCE D'UTILISATION LOGICIELLE</b>", ParagraphStyle('SubSub', parent=title_style, fontSize=12, leading=15, textColor=colors.HexColor('#2563eb'))))
        elements.append(Paragraph(f"Attestation d'acquisition de droit d'exploitation pour le magasin : <b>{store.name}</b>", sub_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=0, spaceAfter=15))

        # Big License Key Box
        key_box_data = [
            [Paragraph("<b>CLÉ D'ACTIVATION OFFICIELLE DU MAGASIN</b>", ParagraphStyle('BoxH', parent=label_style, alignment=1, textColor=colors.HexColor('#1e40af')))],
            [Paragraph(f"<b>{lic.license_key}</b>", key_style)],
            [Paragraph(f"Signature Cryptographique HMAC-SHA256 : <font size='7' color='#64748b'>{lic.signature_hash[:48]}...</font>", ParagraphStyle('SigH', parent=sub_style, fontSize=7.5, spaceAfter=0))]
        ]
        key_table = Table(key_box_data, colWidths=[520])
        key_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#3b82f6')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(key_table)
        elements.append(Spacer(1, 15))

        # License Terms & Parameters
        status_label = "<font color='#16a34a'><b>ACTIVE & VALIDÉE</b></font>" if lic.expires_at >= timezone.now().date() and not lic.is_revoked else "<font color='#dc2626'><b>SUSPENDUE / EXPIRÉE</b></font>"

        info_data = [
            [Paragraph("<b>Paramètre d'Exploitation</b>", label_style), Paragraph("<b>Détail Attribué</b>", label_style)],
            [Paragraph("Magasin Bénéficiaire Acquéreur", label_style), Paragraph(f"<b>{store.name}</b> (Code: #{store.code})", val_style)],
            [Paragraph("Entité / Entreprise Dépositaire", label_style), Paragraph(f"{company.name}", val_style)],
            [Paragraph("Formule / Édition de Licence", label_style), Paragraph(f"<b>{lic.get_plan_type_display()}</b>", val_style)],
            [Paragraph("Nombre de Caisses / Postes Autorisés", label_style), Paragraph(f"<b>{lic.max_registers} caisse(s) enregistreuse(s) simultanée(s)</b>", val_style)],
            [Paragraph("Période de Validité Accordée", label_style), Paragraph(f"Du <b>{lic.valid_from.strftime('%d/%m/%Y')}</b> au <b>{lic.expires_at.strftime('%d/%m/%Y')}</b>", val_style)],
            [Paragraph("Statut d'Homologation", label_style), Paragraph(status_label, val_style)],
            [Paragraph("Localisation Déclarée", label_style), Paragraph(f"{store.address or 'Ouagadougou, Burkina Faso'} (Tél: {store.phone or '+226 --'})", val_style)],
        ]
        info_table = Table(info_data, colWidths=[200, 320])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING', (0, 0), (-1, -1), 5.5),
        ]))
        for h in info_data[0]:
            h.style.textColor = colors.white

        elements.append(info_table)
        elements.append(Spacer(1, 15))

        # Legal Terms
        legal_text = (
            "<b>CONDITIONS GÉNÉRALES D'UTILISATION & RESTRICTIONS LÉGALES :</b><br/>"
            "1. La présente licence confère au magasin bénéficiaire un droit non exclusif et inaliénable d'exploitation de NEXORA Enterprise.<br/>"
            "2. L'utilisation est strictement circonscrite au nombre maximal de caisses enregistreuses et postes de travail souscrits.<br/>"
            "3. Toute tentative de décompilation, modification de clé de contrôle cryptographique ou duplication non autorisée entraîne la révocation immédiate du droit d'accès et des poursuites conformément au code de commerce."
        )
        elements.append(Paragraph(legal_text, ParagraphStyle('Leg', parent=val_style, fontSize=7.5, leading=10.5, textColor=colors.HexColor('#475569'))))
        elements.append(Spacer(1, 20))

        # Signatures
        sig_data = [
            [
                Paragraph("<b>Pour le Magasin Acquéreur</b><br/><br/><br/>Nom du Gérant : ___________________<br/>Cachet & Signature :", val_style),
                Paragraph("<b>Pour l'Éditeur NEXORA Enterprise</b><br/><br/><br/>Direction Commerciale & Juridique<br/>Signature Numérique Certifiée & Sceau :", val_style),
            ]
        ]
        t_sig = Table(sig_data, colWidths=[260, 260])
        t_sig.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(t_sig)

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"Certificat_Licence_{store.code}_{lic.license_key[:10]}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
