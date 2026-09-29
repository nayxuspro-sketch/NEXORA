from django.db import models
from apps.common.models import TenantModel


class PurchaseStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Brouillon'
    ORDERED = 'ORDERED', 'Commandé'
    RECEIVED = 'RECEIVED', 'Reçu / Validé'
    CANCELLED = 'CANCELLED', 'Annulé'


class PurchasePaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'
    PARTIAL = 'PARTIAL', 'Partiellement payé'
    PAID = 'PAID', 'Payé'


class Purchase(TenantModel):
    reference = models.CharField(max_length=100, db_index=True)
    supplier = models.ForeignKey('partners.Partner', on_delete=models.CASCADE, related_name='purchases')
    store = models.ForeignKey('inventory.Store', on_delete=models.CASCADE, related_name='purchases')
    purchaser = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL, related_name='purchases')

    status = models.CharField(max_length=20, choices=PurchaseStatus.choices, default=PurchaseStatus.DRAFT)
    payment_status = models.CharField(max_length=20, choices=PurchasePaymentStatus.choices, default=PurchasePaymentStatus.PENDING)

    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    notes = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = "Achat / Commande Fournisseur"
        verbose_name_plural = "Achats"
        unique_together = ('company', 'reference')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} ({self.total_amount})"


class PurchaseItem(TenantModel):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='purchase_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Ligne d'achat"
        verbose_name_plural = "Lignes d'achat"


class PurchaseReturn(TenantModel):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='returns')
    reference = models.CharField(max_length=100)
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    processed_by = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Retour Fournisseur"
        verbose_name_plural = "Retours Fournisseur"
        unique_together = ('company', 'reference')


class PurchaseReturnItem(TenantModel):
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    refund_total = models.DecimalField(max_digits=12, decimal_places=2)
