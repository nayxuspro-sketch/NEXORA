from django.db import models
from apps.common.models import TenantModel


class Category(TenantModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    description = models.TextField(blank=True, default='')
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='subcategories',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        unique_together = ('company', 'slug')
        ordering = ['name']

    def __str__(self):
        return self.name


class Unit(TenantModel):
    name = models.CharField(max_length=50) # e.g. Pièce, Kilogramme, Litre, Carton
    symbol = models.CharField(max_length=10) # e.g. pcs, kg, L, ctn

    class Meta:
        verbose_name = "Unité de mesure"
        verbose_name_plural = "Unités de mesure"
        unique_together = ('company', 'symbol')

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class Product(TenantModel):
    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(max_length=100, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, default='', db_index=True)
    description = models.TextField(blank=True, default='')
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        related_name='products',
        on_delete=models.SET_NULL
    )
    unit = models.ForeignKey(
        Unit,
        null=True,
        blank=True,
        related_name='products',
        on_delete=models.SET_NULL
    )
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00) # e.g. 18.00%
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        unique_together = ('company', 'sku')
        ordering = ['name']

    def __str__(self):
        return f"{self.sku} - {self.name}"
