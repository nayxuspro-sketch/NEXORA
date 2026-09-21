from decimal import Decimal
from apps.inventory.models import StockMovementType, Inventory, InventoryLine, InventoryStatus, InventoryType
from apps.inventory.services import StockService
from tests.test_nexora_backend import BaseNexoraTestCase
from rest_framework import status

class AdvancedStockAndIntelligenceTests(BaseNexoraTestCase):
    def test_loss_and_damage_movements(self):
        """Test recording loss and damage movements with strict traceability"""
        # Record loss
        m_loss = StockService.record_movement(
            company=self.company_a,
            store=self.store_a,
            product=self.product_a1,
            quantity=Decimal('-3.00'),
            movement_type=StockMovementType.LOSS,
            reference="LOSS-001",
            reason="Vol en magasin constaté"
        )
        self.assertEqual(m_loss.movement_type, StockMovementType.LOSS)
        self.assertEqual(m_loss.quantity, Decimal('-3.00'))

        # Record damage
        m_damage = StockService.record_movement(
            company=self.company_a,
            store=self.store_a,
            product=self.product_a2,
            quantity=Decimal('-2.00'),
            movement_type=StockMovementType.DAMAGE,
            reference="DMG-001",
            reason="Carton endommagé lors du transport"
        )
        self.assertEqual(m_damage.movement_type, StockMovementType.DAMAGE)
        self.assertEqual(m_damage.quantity, Decimal('-2.00'))

    def test_partial_inventory_support(self):
        """Test creation of a partial rotating inventory"""
        inv = Inventory.objects.create(
            company=self.company_a,
            store=self.store_a,
            reference="INV-ROTATING-01",
            inventory_type=InventoryType.PARTIAL,
            created_by=self.user_a
        )
        self.assertEqual(inv.inventory_type, InventoryType.PARTIAL)

    def test_stock_intelligence_analytics_endpoint(self):
        """Verify stock intelligence analytics calculates alerts, rotations and forecasts"""
        response = self.client_a.get('/api/v1/inventory/intelligence/?days=30')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('critical_alerts', response.data)
        self.assertIn('replenishment_forecasts', response.data)
        self.assertIn('predictive_notice', response.data)
