from django.db import models
from apps.common.models import TenantModel


class RegisterStatus(models.TextChoices):
    CLOSED = 'CLOSED', 'Fermée'
    OPEN = 'OPEN', 'Ouverte'


class CashRegister(TenantModel):
    store = models.ForeignKey('inventory.Store', on_delete=models.CASCADE, related_name='registers')
    name = models.CharField(max_length=100) # e.g. Caisse 01
    code = models.CharField(max_length=50) # e.g. REG-01
    status = models.CharField(max_length=20, choices=RegisterStatus.choices, default=RegisterStatus.CLOSED)
    current_cashier = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='active_registers'
    )
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Caisse"
        verbose_name_plural = "Caisses"
        unique_together = ('company', 'code')

    def __str__(self):
        return f"{self.name} ({self.store.name})"


class RegisterSession(TenantModel):
    register = models.ForeignKey(CashRegister, on_delete=models.CASCADE, related_name='sessions')
    cashier = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='register_sessions')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_sales_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    difference = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_closed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Session de Caisse"
        verbose_name_plural = "Sessions de Caisse"
        ordering = ['-opened_at']
