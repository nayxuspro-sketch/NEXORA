from django.db import models
from apps.common.models import TenantModel


class TriggerType(models.TextChoices):
    STOCK_BELOW_THRESHOLD = 'STOCK_BELOW_THRESHOLD', 'Stock inférieur au seuil d alerte'
    OVERDUE_INVOICE = 'OVERDUE_INVOICE', 'Facture ou créance impayée depuis X jours'
    LARGE_TRANSACTION = 'LARGE_TRANSACTION', 'Vente dépassant un montant cible'
    INVENTORY_DISCREPANCY = 'INVENTORY_DISCREPANCY', 'Écart important constaté en inventaire'


class ActionType(models.TextChoices):
    CREATE_NOTIFICATION = 'CREATE_NOTIFICATION', 'Créer une notification utilisateur'
    DRAFT_PURCHASE_ORDER = 'DRAFT_PURCHASE_ORDER', 'Générer un bon de commande fournisseur brouillon'
    SEND_EMAIL_ALERT = 'SEND_EMAIL_ALERT', 'Envoyer une alerte par e-mail'
    LOG_AUDIT_WARNING = 'LOG_AUDIT_WARNING', 'Consigner un avertissement dans le journal d audit'


class AutomationRule(TenantModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    trigger_type = models.CharField(max_length=50, choices=TriggerType.choices)
    action_type = models.CharField(max_length=50, choices=ActionType.choices)
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Paramètres de configuration de la condition (ex: {'threshold': 5, 'days_overdue': 15})"
    )
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    execution_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Règle d'Automatisation"
        verbose_name_plural = "Règles d'Automatisation"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.trigger_type} -> {self.action_type})"


class AutomationLog(TenantModel):
    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name='execution_logs')
    executed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='SUCCESS') # SUCCESS, FAILED
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Journal d'Exécution Règle"
        verbose_name_plural = "Journaux d'Exécution Règles"
        ordering = ['-executed_at']
