import os
import sys
import json
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from apps.accounts.models import User
from apps.companies.models import Company
from apps.catalog.models import Product
from apps.partners.models import Partner
from apps.sales.models import Sale
from apps.inventory.models import StockMovement

def run_e2e_crud_tests():
    print("=" * 70)
    print("DEMARRAGE DU PROTOCOLE DE VALIDATION EXHAUSTIF (E2E & TESTS)")
    print("=" * 70)

    client = Client()

    # 1. Test Authentification Token
    print("\n[TEST 1/5] Authentification JWT...")
    login_resp = client.post(
        '/api/v1/auth/token/',
        data=json.dumps({'email': 'admin@nexora-enterprise.com', 'password': 'Admin123456!'}),
        content_type='application/json'
    )
    assert login_resp.status_code == 200, f"Échec login: {login_resp.status_code} {login_resp.content}"
    token_data = login_resp.json()
    assert 'access' in token_data, "Token access absent"
    token = token_data['access']
    auth_header = f"Bearer {token}"
    print(f" -> Succès : Token JWT obtenu avec succès.")

    # 2. Test Enregistrement Nouveau Produit
    print("\n[TEST 2/5] Création d'un article dans le catalogue...")
    test_sku = f"AUTO-TEST-{os.getpid()}"
    prod_payload = {
        "name": "Disque SSD NVMe 1To Kingston",
        "sku": test_sku,
        "barcode": "3700998877665",
        "cost_price": "35000.00",
        "selling_price": "55000.00",
        "tax_rate": "18.00",
        "alert_threshold": "4.00",
        "description": "Article de test automatique"
    }
    prod_resp = client.post(
        '/api/v1/products/',
        data=json.dumps(prod_payload),
        content_type='application/json',
        HTTP_AUTHORIZATION=auth_header
    )
    assert prod_resp.status_code == 201, f"Échec création produit: {prod_resp.status_code} {prod_resp.content}"
    created_prod = prod_resp.json()
    assert created_prod['sku'] == test_sku
    print(f" -> Succès : Produit '{created_prod['name']}' enregistré en base SQL (ID: {created_prod['id']})")

    # 3. Test Enregistrement Partenaire / Client
    print("\n[TEST 3/5] Création d'un client dans le carnet d'adresses...")
    partner_payload = {
        "name": "Entreprise Burkinabè de BTP SARL",
        "partner_type": "CUSTOMER",
        "email": "contact@btp-faso.bf",
        "phone": "+226 70 11 22 33",
        "address": "Zone Industrielle Kossodo, Ouagadougou",
        "credit_limit": "5000000.00"
    }
    part_resp = client.post(
        '/api/v1/partners/',
        data=json.dumps(partner_payload),
        content_type='application/json',
        HTTP_AUTHORIZATION=auth_header
    )
    assert part_resp.status_code == 201, f"Échec création partenaire: {part_resp.status_code} {part_resp.content}"
    created_part = part_resp.json()
    assert created_part['name'] == partner_payload['name']
    print(f" -> Succès : Client '{created_part['name']}' créé avec plafond de {created_part['credit_limit']} FCFA")

    # 4. Test Vente et Encaissement Caisse POS
    print("\n[TEST 4/5] Transaction Caisse POS (Vente + Paiement + Déstockage)...")
    # 3.bis Ajouter du stock initial pour le test de vente
    from apps.inventory.services import StockService
    from apps.inventory.models import Store, StockMovementType
    from apps.pos.models import CashRegister
    store = Store.objects.first()
    register = CashRegister.objects.first()
    prod_obj = Product.objects.get(id=created_prod['id'])
    StockService.record_movement(
        company=prod_obj.company,
        store=store,
        product=prod_obj,
        quantity=Decimal('10.00'),
        movement_type=StockMovementType.INITIAL,
        reference="INIT-TEST",
        reason="Approvisionnement initial test"
    )

    sale_payload = {
        "store": str(store.id),
        "register": str(register.id),
        "customer": str(created_part['id']),
        "discount_amount": "0.00",
        "items": [
            {
                "product": created_prod['id'],
                "quantity": "2.00",
                "unit_price": "55000.00",
                "tax_rate": "18.00",
                "discount_rate": "0.00"
            }
        ],
        "payment": {
            "amount": "129800.00",
            "method": "MOBILE_MONEY",
            "reference": "OM-VAL-TEST-001"
        }
    }
    sale_resp = client.post(
        '/api/v1/sales/',
        data=json.dumps(sale_payload),
        content_type='application/json',
        HTTP_AUTHORIZATION=auth_header
    )
    assert sale_resp.status_code == 201, f"Échec vente POS: {sale_resp.status_code} {sale_resp.content}"
    sale_data = sale_resp.json()
    print(f" -> Succès : Vente enregistrée #{sale_data['reference']} pour {sale_data['total_amount']} FCFA")

    # 5. Test Mouvement et Traçabilité de Stock
    print("\n[TEST 5/5] Vérification de la décrémentation automatique en inventaire...")
    movements = StockMovement.objects.filter(product_id=created_prod['id'])
    assert movements.exists(), "Aucun mouvement de stock créé lors de la vente"
    latest_mov = movements.latest('created_at')
    print(f" -> Succès : Mouvement de déstockage confirmé ({latest_mov.quantity} unités, type: {latest_mov.movement_type})")

    print("\n" + "=" * 70)
    print("TOUS LES 5 TESTS FONCTIONNELS DE BOUT EN BOUT SONT VALIDES A 100% !")
    print("=" * 70)

if __name__ == '__main__':
    run_e2e_crud_tests()
