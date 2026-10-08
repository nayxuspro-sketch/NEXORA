from django.db import models
from apps.common.models import TenantModel


class NotificationType(models.TextChoices):
    LOW_STOCK = 'LOW_STOCK', 'Alerte stock bas'
    SALE_COMPLETED = 'SALE_COMPLETED', 'Vente enregistrée'
    INVENTORY_DISCREPANCY = 'INVENTORY_DISCREPANCY', 'Écart d inventaire'
    SYSTEM = 'SYSTEM', 'Système'


class Notification(TenantModel):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.user.email}"
