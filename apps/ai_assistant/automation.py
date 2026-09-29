from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, F
from django.db import transaction

from apps.inventory.models import StockLevel
from apps.sales.models import Sale, SaleStatus, PaymentStatus
from apps.notifications.models import Notification, NotificationType
from apps.audit.models import AuditLog
from .models import AutomationRule, AutomationLog, TriggerType, ActionType


class AutomationEngine:
    """
    Evaluates 'IF condition -> THEN action' business rules.
    Operates within the tenant boundary.
    """

    @classmethod
    @transaction.atomic
    def evaluate_rules_for_company(cls, company, user=None):
        rules = AutomationRule.objects.filter(company=company, is_active=True)
        results = []

        for rule in rules:
            try:
                triggered = False
                event_summary = {}

                # 1. TRIGGER: Stock Below Threshold
                if rule.trigger_type == TriggerType.STOCK_BELOW_THRESHOLD:
                    low_stocks = StockLevel.objects.filter(
                        company=company,
                        quantity__lte=F('product__alert_threshold')
                    ).select_related('product', 'store')

                    if low_stocks.exists():
                        triggered = True
                        affected_items = [
                            f"{ls.product.name} ({ls.quantity} pcs @ {ls.store.name})"
                            for ls in low_stocks[:5]
                        ]
                        event_summary = {
                            'count': low_stocks.count(),
                            'sample_items': affected_items,
                            'message': f"{low_stocks.count()} référence(s) sous le seuil d'alerte."
                        }

                # 2. TRIGGER: Overdue Invoices / Receivables
                elif rule.trigger_type == TriggerType.OVERDUE_INVOICE:
                    days_overdue = int(rule.parameters.get('days_overdue', 15))
                    threshold_date = timezone.now() - timedelta(days=days_overdue)
                    unpaid_sales = Sale.objects.filter(
                        company=company,
                        status=SaleStatus.COMPLETED,
                        payment_status__in=[PaymentStatus.PENDING, PaymentStatus.PARTIAL],
                        created_at__lte=threshold_date
                    )
                    if unpaid_sales.exists():
                        triggered = True
                        total_unpaid = unpaid_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
                        event_summary = {
                            'unpaid_count': unpaid_sales.count(),
                            'total_unpaid_amount': str(total_unpaid),
                            'days_overdue': days_overdue,
                            'message': f"{unpaid_sales.count()} vente(s) avec solde impayé depuis plus de {days_overdue} jours."
                        }

                # If rule conditions are met, execute defined action
                if triggered:
                    cls._execute_action(company, rule, event_summary, user)
                    rule.last_triggered_at = timezone.now()
                    rule.execution_count += 1
                    rule.save()

                    log = AutomationLog.objects.create(
                        company=company,
                        rule=rule,
                        status='SUCCESS',
                        details=event_summary
                    )
                    results.append({'rule_id': str(rule.id), 'rule_name': rule.name, 'executed': True, 'details': event_summary})

            except Exception as e:
                AutomationLog.objects.create(
                    company=company,
                    rule=rule,
                    status='FAILED',
                    details={'error': str(e)}
                )
                results.append({'rule_id': str(rule.id), 'rule_name': rule.name, 'executed': False, 'error': str(e)})

        return results

    @classmethod
    def _execute_action(cls, company, rule, event_summary, user=None):
        # Action: Create Notification
        if rule.action_type == ActionType.CREATE_NOTIFICATION:
            target_user = user or company.users.filter(role__in=['ADMIN', 'MANAGER']).first()
            if target_user:
                Notification.objects.create(
                    company=company,
                    user=target_user,
                    notification_type=NotificationType.LOW_STOCK if rule.trigger_type == TriggerType.STOCK_BELOW_THRESHOLD else NotificationType.SYSTEM,
                    title=f"Automatisation : {rule.name}",
                    message=event_summary.get('message', 'Règle exécutée avec succès.')
                )

        # Action: Log Audit Warning
        elif rule.action_type == ActionType.LOG_AUDIT_WARNING:
            AuditLog.objects.create(
                company=company,
                action='AUTOMATION_ALERT',
                resource_type='AutomationRule',
                resource_id=str(rule.id),
                user=user,
                details=event_summary
            )
