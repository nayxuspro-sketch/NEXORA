from django.db import models
from apps.common.models import TenantModel


class Store(TenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    address = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    manager = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        related_name='managed_stores',
        on_delete=models.SET_NULL
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Magasin / Entrepôt"
        verbose_name_plural = "Magasins / Entrepôts"
        unique_together = ('company', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class StockMovementType(models.TextChoices):
    PURCHASE = 'PURCHASE', 'Achat / Réception'
    SALE = 'SALE', 'Vente'
    RETURN_CUSTOMER = 'RETURN_CUSTOMER', 'Retour client'
    RETURN_SUPPLIER = 'RETURN_SUPPLIER', 'Retour fournisseur'
    TRANSFER_IN = 'TRANSFER_IN', 'Transfert entrant'
    TRANSFER_OUT = 'TRANSFER_OUT', 'Transfert sortant'
    ADJUSTMENT_IN = 'ADJUSTMENT_IN', 'Ajustement positif'
    ADJUSTMENT_OUT = 'ADJUSTMENT_OUT', 'Ajustement négatif'
    LOSS = 'LOSS', 'Perte'
    DAMAGE = 'DAMAGE', 'Casse / Dépréciation'
    INITIAL = 'INITIAL', 'Stock initial'


class StockLevel(TenantModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stock_levels')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='stock_levels')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Niveau de stock"
        verbose_name_plural = "Niveaux de stock"
        unique_together = ('store', 'product')
        indexes = [
            models.Index(fields=['company', 'store', 'product']),
        ]

    def __str__(self):
        return f"{self.product.name} @ {self.store.name}: {self.quantity}"


class StockMovement(TenantModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='movements')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=30, choices=StockMovementType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2) # positive for IN, negative for OUT
    quantity_before = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    quantity_after = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reference = models.CharField(max_length=150, blank=True, default='') # Invoice/Sale/PO number
    reason = models.TextField(blank=True, default='')
    user = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL, related_name='stock_movements')

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.movement_type}] {self.product.sku} ({self.quantity}) @ {self.store.code}"


class InventoryStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Brouillon'
    IN_PROGRESS = 'IN_PROGRESS', 'En cours'
    VALIDATED = 'VALIDATED', 'Validé / Clôturé'
    CANCELLED = 'CANCELLED', 'Annulé'


class InventoryType(models.TextChoices):
    FULL = 'FULL', 'Inventaire complet'
    PARTIAL = 'PARTIAL', 'Inventaire tournant / partiel'


class Inventory(TenantModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='inventories')
    reference = models.CharField(max_length=100)
    inventory_type = models.CharField(
        max_length=20,
        choices=InventoryType.choices,
        default=InventoryType.FULL
    )
    status = models.CharField(max_length=20, choices=InventoryStatus.choices, default=InventoryStatus.DRAFT)
    notes = models.TextField(blank=True, default='')
    validated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL, related_name='created_inventories')

    class Meta:
        verbose_name = "Inventaire"
        verbose_name_plural = "Inventaires"
        unique_together = ('company', 'reference')
        ordering = ['-created_at']


class InventoryLine(TenantModel):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='inventory_lines')
    expected_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    counted_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    difference = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = "Ligne d'inventaire"
        verbose_name_plural = "Lignes d'inventaire"
        unique_together = ('inventory', 'product')
