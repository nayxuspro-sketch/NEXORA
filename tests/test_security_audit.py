from decimal import Decimal
from apps.accounts.models import User, UserRole
from apps.pos.models import CashRegister
from apps.audit.models import AuditLog
from apps.catalog.models import Product
from tests.test_nexora_backend import BaseNexoraTestCase
from rest_framework import status


class PenetrationAndSecurityAuditTests(BaseNexoraTestCase):
    """
    Controlled attack scenarios & penetration tests:
    1. Cross-tenant leakage & IDOR (Insecure Direct Object Reference)
    2. Privilege Escalation (Non-admin attempting to change role to ADMIN)
    3. Unauthorized store/cashier manipulation
    4. SQL Injection payload rejection in search fields
    5. Automatic security audit logging of mutating actions and 403s
    """

    def setUp(self):
        super().setUp()
        # Create cashier in Company A
        self.cashier_a = User.objects.create_user(
            email="cashier.sec@alpha.com",
            password="Password123!",
            company=self.company_a,
            role=UserRole.CASHIER
        )
        self.client_cashier = self.client_a
        self.client_cashier.force_authenticate(user=self.cashier_a)

    def test_idor_cross_tenant_patch_product(self):
        """Attacker from company A tries to PATCH product from company B via direct ID"""
        payload = {'selling_price': '1.00'}
        response = self.client_cashier.patch(f'/api/v1/products/{self.product_b1.id}/', payload, format='json')
        # Must be 404 Not Found to prevent leaking object existence
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_privilege_escalation_blocked(self):
        """Cashier tries to promote themselves to ADMIN role"""
        payload = {'role': UserRole.ADMIN}
        response = self.client_cashier.patch(f'/api/v1/users/{self.cashier_a.id}/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.cashier_a.refresh_from_db()
        self.assertEqual(self.cashier_a.role, UserRole.CASHIER)

    def test_cashier_cannot_create_new_user(self):
        """Cashier tries to create a new user in the tenant"""
        payload = {
            'email': 'evil.admin@alpha.com',
            'password': 'Password123!',
            'role': UserRole.ADMIN,
            'first_name': 'Evil',
            'last_name': 'Admin'
        }
        response = self.client_cashier.post('/api/v1/users/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sql_injection_payload_in_search(self):
        """Search query with SQL injection payloads should safely execute without errors"""
        sqli_payload = "'; DROP TABLE apps_catalog_product; --"
        response = self.client_cashier.get(f'/api/v1/products/?search={sqli_payload}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify table still exists and data is intact
        self.assertTrue(Product.objects.filter(id=self.product_a1.id).exists())

    def test_audit_log_records_permission_denied_attempt(self):
        """Audit middleware records 403 Forbidden attack attempts in AuditLog"""
        AuditLog.objects.filter(company=self.company_a).delete()
        # Attempt forbidden action
        payload = {'role': UserRole.ADMIN}
        self.client_cashier.patch(f'/api/v1/users/{self.cashier_a.id}/', payload, format='json')

        # Check audit log
        log_entry = AuditLog.objects.filter(company=self.company_a, action='PERMISSION_DENIED_ATTEMPT').first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.user, self.cashier_a)
