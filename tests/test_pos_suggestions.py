from decimal import Decimal
from apps.pos.suggestions import SmartSuggestionsView
from tests.test_nexora_backend import BaseNexoraTestCase
from rest_framework import status

class SmartPosSuggestionsTests(BaseNexoraTestCase):
    def test_suggestions_endpoint(self):
        response = self.client_a.get(f'/api/v1/pos/suggestions/?product_id={self.product_a1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('frequently_bought_together', response.data)
        self.assertIn('trending_products', response.data)
        self.assertIn('active_promotions', response.data)
