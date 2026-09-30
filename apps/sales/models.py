from django.db import models
from apps.common.models import TenantModel


class SaleStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Brouillon'
    COMPLETED = 'COMPLETED', 'Validée / Complétée'
    CANCELLED = 'CANCELLED', 'Annulée'


class PaymentMethod(models.TextChoices):
    CASH = 'CASH', 'Espèces'
    CARD = 'CARD', 'Carte bancaire'
    MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Virement bancaire'
    CHECK = 'CHECK', 'Chèque'
    CREDIT = 'CREDIT', 'À crédit'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'
    PARTIAL = 'PARTIAL', 'Partiellement payé'
    PAID = 'PAID', 'Payé'
    REFUNDED = 'REFUNDED', 'Remboursé'


class Sale(TenantModel):
    reference = models.CharField(max_length=100, db_index=True)
    store = models.ForeignKey('inventory.Store', on_delete=models.CASCADE, related_name='sales')
    register = models.ForeignKey('pos.CashRegister', null=True, blank=True, on_delete=models.SET_NULL, related_name='sales')
    customer = models.ForeignKey('partners.Partner', null=True, blank=True, on_delete=models.SET_NULL, related_name='sales')
    seller = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL, related_name='sales')

    status = models.CharField(max_length=20, choices=SaleStatus.choices, default=SaleStatus.DRAFT)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    notes = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        unique_together = ('company', 'reference')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} ({self.total_amount})"


class SaleItem(TenantModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='sale_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Ligne de vente"
        verbose_name_plural = "Lignes de vente"


class Payment(TenantModel):
    sale = models.ForeignKey(Sale, null=True, blank=True, on_delete=models.CASCADE, related_name='payments')
    purchase = models.ForeignKey('purchases.Purchase', null=True, blank=True, on_delete=models.CASCADE, related_name='payments')
    partner = models.ForeignKey('partners.Partner', null=True, blank=True, on_delete=models.SET_NULL, related_name='payments')
    register = models.ForeignKey('pos.CashRegister', null=True, blank=True, on_delete=models.SET_NULL, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    reference = models.CharField(max_length=100, blank=True, default='')
    processed_by = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']


class SaleReturn(TenantModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    reference = models.CharField(max_length=100)
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    processed_by = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Retour Vente"
        verbose_name_plural = "Retours Vente"
        unique_together = ('company', 'reference')


class SaleReturnItem(TenantModel):
    sale_return = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    refund_total = models.DecimalField(max_digits=12, decimal_places=2)
