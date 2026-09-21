from django.db import models
from apps.common.models import TimeStampedModel


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
