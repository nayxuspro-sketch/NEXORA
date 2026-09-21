from django.db import models
from apps.common.models import TenantModel


class AuditLog(TenantModel):
    action = models.CharField(max_length=100) # CREATE, UPDATE, DELETE, CANCEL, VALIDATE
    resource_type = models.CharField(max_length=100) # Sale, Purchase, StockMovement, User
    resource_id = models.CharField(max_length=100, blank=True, default='')
    user = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL, related_name='audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.action}] {self.resource_type} ({self.resource_id}) par {self.user}"
