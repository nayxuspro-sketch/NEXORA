from decimal import Decimal
from apps.reports.bi_analytics import BusinessIntelligenceAnalyticsView
from tests.test_nexora_backend import BaseNexoraTestCase
from rest_framework import status

class BusinessIntelligenceTests(BaseNexoraTestCase):
    def test_bi_analytics_endpoint_general(self):
        """Test BI endpoint returns sales, profitability, stock health, and data-driven explanations"""
        response = self.client_a.get('/api/v1/reports/bi-analytics/?days=30&view=executive')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('insights_explanation', response.data)
        self.assertIn('sales_overview', response.data)
        self.assertIn('profitability', response.data)
        self.assertIn('stock_health', response.data)
        self.assertIn('customer_insights', response.data)

    def test_bi_analytics_role_views(self):
        """Test different role-oriented perspectives (manager, sales, stock, cashier)"""
        for view_name in ['executive', 'manager', 'sales', 'stock', 'cashier']:
            response = self.client_a.get(f'/api/v1/reports/bi-analytics/?view={view_name}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['requested_view'], view_name)
