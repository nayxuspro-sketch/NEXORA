from django.db import models
from django.utils import timezone
from apps.common.models import TimeStampedModel, TenantModel


class Company(TimeStampedModel):
    """
    Tenant representation in NEXORA.
    Each company has isolated data: stores, sales, stock, users, etc.
    """
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    registration_number = models.CharField(max_length=100, blank=True, default='')
    tax_identifier = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    address = models.TextField(blank=True, default='')
    currency = models.CharField(max_length=10, default='XOF') # FCFA (BCEAO - Burkina Faso / UEMOA)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        ordering = ['name']

    def __str__(self):
        return self.name


class StoreLicense(TenantModel):
    store = models.ForeignKey('inventory.Store', on_delete=models.CASCADE, related_name='licenses')
    license_key = models.CharField(max_length=255, unique=True)
    plan_type = models.CharField(
        max_length=50,
        choices=[
            ('STANDARD', 'Standard Caisse & Stock (1 Poste)'),
            ('PRO', 'Professionnel Multi-Caisses (3 Postes)'),
            ('ENTERPRISE', 'Entreprise Illimitée & BI Analytics'),
        ],
        default='PRO'
    )
    max_registers = models.PositiveIntegerField(default=3)
    issued_to_name = models.CharField(max_length=255)
    valid_from = models.DateField(default=timezone.now)
    expires_at = models.DateField()
    signature_hash = models.CharField(max_length=255)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.store.name} - {self.license_key}"
