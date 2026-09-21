from django.db import models
from apps.common.models import TenantModel


class PartnerType(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Client'
    SUPPLIER = 'SUPPLIER', 'Fournisseur'
    BOTH = 'BOTH', 'Client & Fournisseur'


class Partner(TenantModel):
    name = models.CharField(max_length=255, db_index=True)
    partner_type = models.CharField(
        max_length=20,
        choices=PartnerType.choices,
        default=PartnerType.CUSTOMER
    )
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    address = models.TextField(blank=True, default='')
    tax_number = models.CharField(max_length=100, blank=True, default='')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Partenaire (Client / Fournisseur)"
        verbose_name_plural = "Partenaires"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"
