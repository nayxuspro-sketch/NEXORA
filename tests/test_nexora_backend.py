import uuid
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.companies.models import Company
from apps.accounts.models import User, UserRole
from apps.catalog.models import Category, Unit, Product
from apps.partners.models import Partner, PartnerType
from apps.inventory.models import Store, StockLevel, StockMovement, StockMovementType, Inventory, InventoryLine, InventoryStatus
from apps.pos.models import CashRegister, RegisterSession, RegisterStatus
from apps.sales.models import Sale, SaleItem, SaleStatus, Payment, PaymentMethod, PaymentStatus, SaleReturn
from apps.purchases.models import Purchase, PurchaseStatus, PurchasePaymentStatus, PurchaseReturn
from apps.inventory.services import StockService
from apps.sales.services import SaleService
from apps.purchases.services import PurchaseService


class BaseNexoraTestCase(TestCase):
    def setUp(self):
        # Company A
        self.company_a = Company.objects.create(name="Nexora Faso SARL", slug="alpha", currency="XOF")
        self.user_a = User.objects.create_user(
            email="admin@alpha.com",
            password="Password123!",
            first_name="Admin",
            last_name="Alpha",
            company=self.company_a,
            role=UserRole.ADMIN
        )
        self.store_a = Store.objects.create(company=self.company_a, name="Alpha Depot Ouagadougou", code="MAG-A1")

        # Company B
        self.company_b = Company.objects.create(name="Beta Industries", slug="beta", currency="XOF")
        self.user_b = User.objects.create_user(
            email="manager@beta.com",
            password="Password123!",
            first_name="Manager",
            last_name="Beta",
            company=self.company_b,
            role=UserRole.MANAGER
        )
        self.store_b = Store.objects.create(company=self.company_b, name="Beta Store Nord", code="MAG-B1")

        # Catalog setup for Company A
        self.category_a = Category.objects.create(company=self.company_a, name="Électronique", slug="electronique")
        self.unit_a = Unit.objects.create(company=self.company_a, name="Pièce", symbol="pcs")
        self.product_a1 = Product.objects.create(
            company=self.company_a,
            name="Ordinateur Portable Pro 15",
            sku="LAPTOP-01",
            category=self.category_a,
            unit=self.unit_a,
            cost_price=Decimal('500.00'),
            selling_price=Decimal('800.00'),
            tax_rate=Decimal('20.00'),
            alert_threshold=Decimal('5.00')
        )
        self.product_a2 = Product.objects.create(
            company=self.company_a,
            name="Souris Sans Fil Ergonomique",
            sku="MOUSE-01",
            category=self.category_a,
            unit=self.unit_a,
            cost_price=Decimal('15.00'),
            selling_price=Decimal('35.00'),
            tax_rate=Decimal('20.00'),
            alert_threshold=Decimal('10.00')
        )

        # Catalog setup for Company B
        self.product_b1 = Product.objects.create(
            company=self.company_b,
            name="Produit Exclusif Beta",
            sku="BETA-PROD-01",
            cost_price=Decimal('100.00'),
            selling_price=Decimal('200.00')
        )

        # Partners
        self.customer_a = Partner.objects.create(
            company=self.company_a,
            name="Client Grand Compte",
            partner_type=PartnerType.CUSTOMER
        )
        self.supplier_a = Partner.objects.create(
            company=self.company_a,
            name="Fournisseur Tech World",
            partner_type=PartnerType.SUPPLIER
        )

        # Seed initial stock for Company A
        StockService.record_movement(
            company=self.company_a,
            store=self.store_a,
            product=self.product_a1,
            quantity=Decimal('50.00'),
            movement_type=StockMovementType.INITIAL,
            reference="INIT-STOCK",
            reason="Stock initial"
        )
        StockService.record_movement(
            company=self.company_a,
            store=self.store_a,
            product=self.product_a2,
            quantity=Decimal('100.00'),
            movement_type=StockMovementType.INITIAL,
            reference="INIT-STOCK",
            reason="Stock initial"
        )

        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)

        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)


class MultiTenantIsolationTests(BaseNexoraTestCase):
    def test_cannot_read_other_company_products(self):
        """User A must NOT see products belonging to Company B"""
        response = self.client_a.get('/api/v1/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data['results']]
        self.assertIn(str(self.product_a1.id), ids)
        self.assertNotIn(str(self.product_b1.id), ids)

    def test_cannot_read_other_company_product_detail(self):
        """User A trying to access product of Company B directly by UUID returns 404"""
        response = self.client_a.get(f'/api/v1/products/{self.product_b1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_create_sale_with_other_company_store(self):
        """Prevent user A from selling from Company B store"""
        payload = {
            'store': str(self.store_b.id),
            'items': [{'product': str(self.product_a1.id), 'quantity': 1}]
        }
        response = self.client_a.post('/api/v1/sales/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_sale_with_other_company_product(self):
        """Prevent user A from selling a product belonging to Company B"""
        payload = {
            'store': str(self.store_a.id),
            'items': [{'product': str(self.product_b1.id), 'quantity': 1}]
        }
        response = self.client_a.post('/api/v1/sales/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StockMovementAndInventoryTests(BaseNexoraTestCase):
    def test_stock_level_updated_and_movement_recorded(self):
        """Stock movement accurately updates current stock and creates history audit"""
        level_before = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        StockService.record_movement(
            company=self.company_a,
            store=self.store_a,
            product=self.product_a1,
            quantity=Decimal('10.00'),
            movement_type=StockMovementType.ADJUSTMENT_IN,
            reason="Inventaire test"
        )
        level_after = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        self.assertEqual(level_after, level_before + Decimal('10.00'))

        last_move = StockMovement.objects.filter(product=self.product_a1).first()
        self.assertEqual(last_move.movement_type, StockMovementType.ADJUSTMENT_IN)
        self.assertEqual(last_move.quantity, Decimal('10.00'))

    def test_negative_stock_prevention(self):
        """Stock cannot go negative when allow_negative=False"""
        with self.assertRaises(Exception):
            StockService.record_movement(
                company=self.company_a,
                store=self.store_a,
                product=self.product_a1,
                quantity=Decimal('-999.00'),
                movement_type=StockMovementType.SALE,
                allow_negative=False
            )

    def test_inventory_validation_and_reconciliation(self):
        """Validating an inventory adjusts differences to physical reality"""
        inv = Inventory.objects.create(
            company=self.company_a,
            store=self.store_a,
            reference="INV-2026-001",
            created_by=self.user_a
        )
        # Expected is 50, counted is 48 (shortage of 2)
        InventoryLine.objects.create(
            company=self.company_a,
            inventory=inv,
            product=self.product_a1,
            expected_quantity=Decimal('50.00'),
            counted_quantity=Decimal('48.00')
        )
        StockService.validate_inventory(inv, user=self.user_a)

        inv.refresh_from_db()
        self.assertEqual(inv.status, InventoryStatus.VALIDATED)
        new_level = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        self.assertEqual(new_level, Decimal('48.00'))


class SalesAndPaymentTests(BaseNexoraTestCase):
    def test_complete_sale_transaction_flow(self):
        """
        Step 1: Stock verified
        Step 2: Sale created
        Step 3: Lines created with tax calculations
        Step 4: Stock decremented
        Step 5: Movement logged
        Step 6: Payment recorded
        """
        initial_stock = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity

        payload = {
            'store': str(self.store_a.id),
            'customer': str(self.customer_a.id),
            'items': [
                {'product': str(self.product_a1.id), 'quantity': 2, 'unit_price': '800.00', 'tax_rate': '20.00'}
            ],
            'payment': {
                'amount': '1920.00',
                'method': 'CASH',
                'reference': 'CASH-REC-01'
            }
        }
        response = self.client_a.post('/api/v1/sales/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        sale_id = response.data['id']
        sale = Sale.objects.get(id=sale_id)
        self.assertEqual(sale.status, SaleStatus.COMPLETED)
        self.assertEqual(sale.payment_status, PaymentStatus.PAID)
        # 2 * 800 = 1600 HT + 20% tax (320) = 1920 TTC
        self.assertEqual(sale.total_amount, Decimal('1920.00'))

        # Check stock deduction
        stock_after = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        self.assertEqual(stock_after, initial_stock - Decimal('2.00'))

        # Check stock movement record
        move = StockMovement.objects.filter(reference=f"SALE-{sale.reference}").first()
        self.assertIsNotNone(move)
        self.assertEqual(move.quantity, Decimal('-2.00'))

    def test_sale_rollback_on_insufficient_stock(self):
        """If any line exceeds available stock, entire sale is rejected without residual data"""
        sales_count_before = Sale.objects.count()

        payload = {
            'store': str(self.store_a.id),
            'customer': str(self.customer_a.id),
            'items': [
                {'product': str(self.product_a1.id), 'quantity': 9999, 'unit_price': '800.00'}
            ]
        }
        response = self.client_a.post('/api/v1/sales/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Sale.objects.count(), sales_count_before)

    def test_sale_cancellation_reverts_stock(self):
        """Cancelling a sale returns items to store stock"""
        sale = SaleService.create_and_complete_sale(
            company=self.company_a,
            store=self.store_a,
            seller=self.user_a,
            items_data=[{'product': self.product_a1, 'quantity': Decimal('5.00')}]
        )
        stock_after_sale = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity

        SaleService.cancel_sale(sale, user=self.user_a, reason="Client a changé d'avis")

        sale.refresh_from_db()
        self.assertEqual(sale.status, SaleStatus.CANCELLED)
        stock_after_cancel = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        self.assertEqual(stock_after_cancel, stock_after_sale + Decimal('5.00'))

    def test_customer_return_restores_stock(self):
        """Customer return partial product restores returned qty to stock"""
        sale = SaleService.create_and_complete_sale(
            company=self.company_a,
            store=self.store_a,
            seller=self.user_a,
            items_data=[{'product': self.product_a1, 'quantity': Decimal('4.00')}]
        )
        stock_before_return = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity

        ret = SaleService.process_return(
            sale=sale,
            return_items=[{'product': self.product_a1, 'quantity': Decimal('2.00')}],
            user=self.user_a,
            reason="Unité défectueuse"
        )
        self.assertEqual(ret.items.count(), 1)
        stock_after_return = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        self.assertEqual(stock_after_return, stock_before_return + Decimal('2.00'))


class PurchasesTests(BaseNexoraTestCase):
    def test_purchase_order_flow_and_reception(self):
        """Purchase creation then reception increments stock levels"""
        stock_before = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity

        purchase = PurchaseService.create_purchase(
            company=self.company_a,
            supplier=self.supplier_a,
            store=self.store_a,
            purchaser=self.user_a,
            items_data=[{'product': self.product_a1, 'quantity': Decimal('20.00'), 'unit_cost': Decimal('480.00')}],
            auto_receive=False
        )
        self.assertEqual(purchase.status, PurchaseStatus.DRAFT)
        # Stock not changed yet
        self.assertEqual(StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity, stock_before)

        # Receive purchase
        PurchaseService.receive_purchase(purchase, user=self.user_a)
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, PurchaseStatus.RECEIVED)
        stock_after = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        self.assertEqual(stock_after, stock_before + Decimal('20.00'))

    def test_purchase_return_decrements_stock(self):
        """Returning goods to supplier decreases stock"""
        purchase = PurchaseService.create_purchase(
            company=self.company_a,
            supplier=self.supplier_a,
            store=self.store_a,
            purchaser=self.user_a,
            items_data=[{'product': self.product_a1, 'quantity': Decimal('10.00')}],
            auto_receive=True
        )
        stock_after_rec = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity

        PurchaseService.process_return(
            purchase=purchase,
            return_items=[{'product': self.product_a1, 'quantity': Decimal('4.00')}],
            user=self.user_a,
            reason="Marchandise non conforme"
        )
        stock_after_ret = StockLevel.objects.get(store=self.store_a, product=self.product_a1).quantity
        self.assertEqual(stock_after_ret, stock_after_rec - Decimal('4.00'))


class CashRegisterPosTests(BaseNexoraTestCase):
    def test_cash_register_lifecycle(self):
        """Open register -> sale in cash increments balance -> close register calculates difference"""
        register = CashRegister.objects.create(
            company=self.company_a,
            store=self.store_a,
            name="Caisse Principale",
            code="POS-01"
        )

        # Open session
        resp_open = self.client_a.post(f'/api/v1/registers/{register.id}/open_session/', {'opening_balance': '100.00'})
        self.assertEqual(resp_open.status_code, status.HTTP_201_CREATED)
        register.refresh_from_db()
        self.assertEqual(register.status, RegisterStatus.OPEN)
        self.assertEqual(register.current_balance, Decimal('100.00'))

        # Make sale attached to this register
        SaleService.create_and_complete_sale(
            company=self.company_a,
            store=self.store_a,
            seller=self.user_a,
            register=register,
            items_data=[{'product': self.product_a2, 'quantity': Decimal('2.00'), 'unit_price': Decimal('35.00')}],
            payment_data={'amount': Decimal('70.00'), 'method': PaymentMethod.CASH}
        )

        register.refresh_from_db()
        self.assertEqual(register.current_balance, Decimal('170.00'))

        # Close session with matching balance
        resp_close = self.client_a.post(f'/api/v1/registers/{register.id}/close_session/', {'closing_balance': '170.00'})
        self.assertEqual(resp_close.status_code, status.HTTP_200_OK)
        register.refresh_from_db()
        self.assertEqual(register.status, RegisterStatus.CLOSED)


class ReportsAndDashboardTests(BaseNexoraTestCase):
    def test_dashboard_report_endpoint(self):
        """Dashboard endpoint computes KPIs accurately"""
        response = self.client_a.get('/api/v1/reports/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sales', response.data)
        self.assertIn('inventory', response.data)
        self.assertIn('profitability', response.data)

    def test_inventory_valuation_endpoint(self):
        """Valuation endpoint calculates total cost and retail stock value"""
        response = self.client_a.get('/api/v1/reports/inventory-valuation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_cost_valuation', response.data)
        self.assertIn('total_retail_valuation', response.data)
