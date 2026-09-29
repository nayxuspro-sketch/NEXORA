from decimal import Decimal
from apps.accounts.models import User, UserRole
from apps.inventory.models import StockLevel
from apps.ai_assistant.models import AutomationRule, TriggerType, ActionType
from apps.ai_assistant.automation import AutomationEngine
from apps.notifications.models import Notification
from tests.test_nexora_backend import BaseNexoraTestCase
from rest_framework import status

class AIAssistantAndAutomationTests(BaseNexoraTestCase):
    def test_ai_chat_today_sales(self):
        """AI Assistant answers questions about today's sales"""
        response = self.client_a.post('/api/v1/ai/chat/', {'question': "Combien ai-je vendu aujourd'hui ?"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)
        self.assertIn('explanation', response.data)

    def test_ai_chat_shortage_risks(self):
        """AI Assistant identifies shortage risks and explains reasoning"""
        response = self.client_a.post('/api/v1/ai/chat/', {'question': "Quels produits risquent de manquer ?"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)

    def test_ai_security_rbac_restriction(self):
        """Cashier role is strictly forbidden from viewing company profit data via AI"""
        cashier_user = User.objects.create_user(
            email="cashier.test@alpha.com",
            password="Password123!",
            company=self.company_a,
            role=UserRole.CASHIER
        )
        self.client_a.force_authenticate(user=cashier_user)

        response = self.client_a.post('/api/v1/ai/chat/', {'question': "Quels sont mes produits les plus rentables ?"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('role_blocked'))
        self.assertIn("Accès restreint", response.data['answer'])

    def test_automation_rules_engine_stock_trigger(self):
        """Test automation engine: IF stock < threshold -> THEN create notification"""
        # Lower stock of product_a1 below alert threshold (alert_threshold is 5.00)
        lvl = StockLevel.objects.get(store=self.store_a, product=self.product_a1)
        lvl.quantity = Decimal('2.00')
        lvl.save()

        # Create rule
        rule = AutomationRule.objects.create(
            company=self.company_a,
            name="Alerte Stock Bas",
            trigger_type=TriggerType.STOCK_BELOW_THRESHOLD,
            action_type=ActionType.CREATE_NOTIFICATION
        )

        # Trigger engine
        notif_count_before = Notification.objects.filter(company=self.company_a).count()
        results = AutomationEngine.evaluate_rules_for_company(self.company_a, user=self.user_a)

        self.assertGreaterEqual(len(results), 1)
        rule.refresh_from_db()
        self.assertEqual(rule.execution_count, 1)
