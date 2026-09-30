import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from apps.companies.models import Company
from apps.accounts.models import User, UserRole
from apps.catalog.models import Category, Unit, Product
from apps.partners.models import Partner, PartnerType
from apps.inventory.models import Store, StockMovementType
from apps.inventory.services import StockService
from apps.pos.models import CashRegister, RegisterStatus
from apps.sales.services import SaleService
from apps.sales.models import Sale, PaymentMethod
from apps.ai_assistant.models import AutomationRule, TriggerType, ActionType

def seed_demo_data():
    print("Seed: Initialisation des données de démonstration NEXORA (Burkina Faso / FCFA)...")
    
    # 1. Company
    company, _ = Company.objects.get_or_create(
        slug="nexora-faso",
        defaults={
            "name": "NEXORA BURKINA COMMERCIAL GROUP",
            "currency": "XOF",
            "email": "contact@nexora-bf.com",
            "phone": "+226 25 30 60 70",
            "address": "Avenue Kwamé N'Krumah, Ouagadougou, Burkina Faso"
        }
    )

    # 2. Users (Admin, Manager, Cashier)
    admin_user = User.objects.filter(email="admin@nexora-enterprise.com").first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            email="admin@nexora-enterprise.com",
            password="Admin123456!",
            first_name="Directeur",
            last_name="Général",
            company=company,
            role=UserRole.ADMIN
        )
    else:
        admin_user.set_password("Admin123456!")
        admin_user.company = company
        admin_user.save()

    cashier_user = User.objects.filter(email="caissier@nexora-bf.com").first()
    if not cashier_user:
        cashier_user = User.objects.create_user(
            email="caissier@nexora-bf.com",
            password="Cashier123!",
            first_name="Ibrahim",
            last_name="Ouedraogo",
            company=company,
            role=UserRole.CASHIER
        )
    else:
        cashier_user.set_password("Cashier123!")
        cashier_user.company = company
        cashier_user.save()

    # 3. Store
    store, _ = Store.objects.get_or_create(
        company=company,
        code="MAG-OUAGA-01",
        defaults={
            "name": "Magasin & Dépôt Ouaga Central",
            "address": "Avenue Kwamé N'Krumah, Ouagadougou",
            "phone": "+226 25 31 10 20",
            "manager": admin_user
        }
    )

    # 4. Cash Register
    register, _ = CashRegister.objects.get_or_create(
        company=company,
        code="REG-01",
        defaults={
            "store": store,
            "name": "Caisse Comptoir Principal",
            "status": RegisterStatus.OPEN,
            "current_cashier": cashier_user,
            "opening_balance": Decimal('50000.00'),
            "current_balance": Decimal('125000.00')
        }
    )

    # 5. Catalog in FCFA
    cat_pc, _ = Category.objects.get_or_create(company=company, slug="ordinateurs", defaults={"name": "Informatique & PC"})
    cat_periph, _ = Category.objects.get_or_create(company=company, slug="peripheriques", defaults={"name": "Périphériques & Accessoires"})
    cat_reseau, _ = Category.objects.get_or_create(company=company, slug="reseaux-telecom", defaults={"name": "Réseaux & Télécoms"})
    cat_bureau, _ = Category.objects.get_or_create(company=company, slug="papeterie-bureau", defaults={"name": "Papeterie & Fournitures"})
    cat_impr, _ = Category.objects.get_or_create(company=company, slug="impression", defaults={"name": "Imprimantes & Toners"})
    cat_stock, _ = Category.objects.get_or_create(company=company, slug="stockage-externe", defaults={"name": "Stockage & Supports"})
    unit_pcs, _ = Unit.objects.get_or_create(company=company, symbol="pcs", defaults={"name": "Pièce"})

    prod1, _ = Product.objects.get_or_create(
        company=company,
        sku="LAPTOP-HP-01",
        defaults={
            "name": "Ordinateur Portable HP ProBook 15",
            "barcode": "3700123456789",
            "description": "Intel Core i5, 16Go RAM, 512Go SSD, Clavier AZERTY",
            "category": cat_pc,
            "unit": unit_pcs,
            "cost_price": Decimal('325000.00'),
            "selling_price": Decimal('450000.00'),
            "tax_rate": Decimal('18.00'), # TVA 18% (Burkina Faso / UEMOA)
            "alert_threshold": Decimal('5.00')
        }
    )

    prod2, _ = Product.objects.get_or_create(
        company=company,
        sku="MOUSE-WL-01",
        defaults={
            "name": "Souris Sans Fil Ergonomique Rechargeable",
            "barcode": "3700123456790",
            "description": "Capteur optique haute précision 2.4GHz",
            "category": cat_periph,
            "unit": unit_pcs,
            "cost_price": Decimal('8000.00'),
            "selling_price": Decimal('15000.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('10.00')
        }
    )

    prod3, _ = Product.objects.get_or_create(
        company=company,
        sku="KEYB-USB-01",
        defaults={
            "name": "Clavier USB Bureautique AZERTY",
            "barcode": "3700123456791",
            "description": "Clavier standard résistant aux éclaboussures",
            "category": cat_periph,
            "unit": unit_pcs,
            "cost_price": Decimal('6500.00'),
            "selling_price": Decimal('12500.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('8.00')
        }
    )

    prod4, _ = Product.objects.get_or_create(
        company=company,
        sku="DISP-DELL-24",
        defaults={
            "name": "Écran Dell 24 Pouces Full HD",
            "barcode": "3700123456792",
            "description": "Dalle IPS HDMI/VGA antireflet",
            "category": cat_periph,
            "unit": unit_pcs,
            "cost_price": Decimal('75000.00'),
            "selling_price": Decimal('110000.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('4.00')
        }
    )

    prod5, _ = Product.objects.get_or_create(
        company=company,
        sku="IMP-CANON-LBP",
        defaults={
            "name": "Imprimante Laser Canon i-SENSYS LBP6030B",
            "barcode": "3700123456801",
            "description": "Imprimante laser monochrome rapide",
            "category": cat_impr,
            "unit": unit_pcs,
            "cost_price": Decimal('65000.00'),
            "selling_price": Decimal('95000.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('5.00')
        }
    )

    prod6, _ = Product.objects.get_or_create(
        company=company,
        sku="TONER-CANON-725",
        defaults={
            "name": "Cartouche de Toner Canon 725 Noir Authentique",
            "barcode": "3700123456802",
            "description": "Toner noir pour Canon LBP6030B",
            "category": cat_impr,
            "unit": unit_pcs,
            "cost_price": Decimal('18000.00'),
            "selling_price": Decimal('28500.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('8.00')
        }
    )

    prod7, _ = Product.objects.get_or_create(
        company=company,
        sku="ROUTEUR-TP-LINK-4G",
        defaults={
            "name": "Routeur Wi-Fi 4G LTE TP-Link TL-MR6400",
            "barcode": "3700123456803",
            "description": "Routeur 4G 300 Mbps avec slot carte SIM",
            "category": cat_reseau,
            "unit": unit_pcs,
            "cost_price": Decimal('32000.00'),
            "selling_price": Decimal('48000.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('6.00')
        }
    )

    prod8, _ = Product.objects.get_or_create(
        company=company,
        sku="CABLE-RJ45-10M",
        defaults={
            "name": "Câble Réseau Ethernet RJ45 Cat6 blindé (10 mètres)",
            "barcode": "3700123456804",
            "description": "Câble RJ45 haute vitesse catégorie 6",
            "category": cat_reseau,
            "unit": unit_pcs,
            "cost_price": Decimal('3000.00'),
            "selling_price": Decimal('6500.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('10.00')
        }
    )

    prod9, _ = Product.objects.get_or_create(
        company=company,
        sku="RAMETTE-DOUBLE-A",
        defaults={
            "name": "Carton 5 Ramettes Papier A4 Double A 80g",
            "barcode": "3700123456805",
            "description": "Papier reprographie haute blancheur",
            "category": cat_bureau,
            "unit": unit_pcs,
            "cost_price": Decimal('16500.00'),
            "selling_price": Decimal('24000.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('15.00')
        }
    )

    prod10, _ = Product.objects.get_or_create(
        company=company,
        sku="DISQUE-EXT-SSD-1TB",
        defaults={
            "name": "Disque SSD Externe SanDisk Extreme 1To USB-C",
            "barcode": "3700123456806",
            "description": "Disque portable résistant aux chocs et chutes",
            "category": cat_stock,
            "unit": unit_pcs,
            "cost_price": Decimal('55000.00'),
            "selling_price": Decimal('79000.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('4.00')
        }
    )

    prod11, _ = Product.objects.get_or_create(
        company=company,
        sku="CLE-USB-SANDISK-64G",
        defaults={
            "name": "Clé USB 3.0 SanDisk Ultra 64Go Métal",
            "barcode": "3700123456807",
            "description": "Stockage ultra-rapide USB 3.0",
            "category": cat_stock,
            "unit": unit_pcs,
            "cost_price": Decimal('4500.00'),
            "selling_price": Decimal('8500.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('12.00')
        }
    )

    prod12, _ = Product.objects.get_or_create(
        company=company,
        sku="ONDULEUR-APC-650VA",
        defaults={
            "name": "Onduleur APC Back-UPS 650VA avec protection surtension",
            "barcode": "3700123456808",
            "description": "Protection parafoudre et batterie de secours",
            "category": cat_reseau,
            "unit": unit_pcs,
            "cost_price": Decimal('42000.00'),
            "selling_price": Decimal('62000.00'),
            "tax_rate": Decimal('18.00'),
            "alert_threshold": Decimal('5.00')
        }
    )

    # 6. Stocks Setup
    initial_inventory = [
        (prod1, Decimal('15.00')), (prod2, Decimal('40.00')), (prod3, Decimal('30.00')), (prod4, Decimal('10.00')),
        (prod5, Decimal('20.00')), (prod6, Decimal('35.00')), (prod7, Decimal('25.00')), (prod8, Decimal('45.00')),
        (prod9, Decimal('55.00')), (prod10, Decimal('18.00')), (prod11, Decimal('40.00')), (prod12, Decimal('15.00'))
    ]
    for p, qty in initial_inventory:
        from apps.inventory.models import StockLevel
        current_lvl = StockLevel.objects.filter(company=company, store=store, product=p).first()
        if not current_lvl or current_lvl.quantity <= 0:
            StockService.record_movement(
                company=company,
                store=store,
                product=p,
                quantity=qty,
                movement_type=StockMovementType.INITIAL,
                reference="INIT-FASO",
                reason="Stock initial Ouagadougou"
            )

    # 7. Partners (Customer / Supplier)
    cust1, _ = Partner.objects.get_or_create(
        company=company,
        name="Entreprise Faso Services SARL",
        defaults={
            "partner_type": PartnerType.CUSTOMER,
            "email": "contact@faso-services.bf",
            "phone": "+226 25 36 00 22",
            "address": "Quartier Ouaga 2000, Ouagadougou",
            "credit_limit": Decimal('2000000.00'),
            "current_balance": Decimal('0.00')
        }
    )

    # 8. Sample Vente initiale en FCFA (Espèces / Mobile Money Orange Money / Moov Money)
    try:
        SaleService.create_and_complete_sale(
            company=company,
            store=store,
            seller=cashier_user,
            customer=cust1,
            register=register,
            items_data=[
                {'product': prod1, 'quantity': Decimal('1.00')},
                {'product': prod2, 'quantity': Decimal('1.00')}
            ],
            payment_data={'amount': Decimal('465000.00'), 'method': PaymentMethod.MOBILE_MONEY, 'reference': 'OM-BF-892102'}
        )
    except Exception as e:
        print(f"Sample sale note: {e}")

    # Ventes historiques additionnelles pour enrichir l'historique :
    try:
        if Sale.objects.filter(company=company).count() < 8:
            # Vente 2 : Vente comptoir en espèces
            SaleService.create_and_complete_sale(
                company=company,
                store=store,
                seller=cashier_user,
                customer=None,
                register=register,
                items_data=[
                    {'product': prod2, 'quantity': Decimal('2.00')},
                    {'product': prod4, 'quantity': Decimal('1.00')}
                ],
                payment_data={'amount': Decimal('64900.00'), 'method': PaymentMethod.CASH, 'reference': 'ESP-002'}
            )
            # Vente 3 : Équipements informatiques
            SaleService.create_and_complete_sale(
                company=company,
                store=store,
                seller=admin_user,
                customer=cust1,
                register=register,
                items_data=[
                    {'product': prod3, 'quantity': Decimal('2.00')}
                ],
                payment_data={'amount': Decimal('259600.00'), 'method': PaymentMethod.BANK_TRANSFER, 'reference': 'VIR-BF-003'}
            )
            # Vente 4 : Vente avec acompte partiel
            SaleService.create_and_complete_sale(
                company=company,
                store=store,
                seller=cashier_user,
                customer=None,
                register=register,
                items_data=[
                    {'product': prod1, 'quantity': Decimal('1.00')},
                    {'product': prod2, 'quantity': Decimal('1.00')}
                ],
                payment_data={'amount': Decimal('300000.00'), 'method': PaymentMethod.MOBILE_MONEY, 'reference': 'OM-BF-004'}
            )
            # Vente 5 : Fournitures et accessoires
            SaleService.create_and_complete_sale(
                company=company,
                store=store,
                seller=cashier_user,
                customer=cust1,
                register=register,
                items_data=[
                    {'product': prod4, 'quantity': Decimal('5.00')}
                ],
                payment_data={'amount': Decimal('147500.00'), 'method': PaymentMethod.CASH, 'reference': 'ESP-005'}
            )
    except Exception as e:
        print(f"Additional sales note: {e}")

    # 9. Automation Rule
    AutomationRule.objects.get_or_create(
        company=company,
        name="Alerte Stock Bas Ouaga",
        defaults={
            "description": "Notifie automatiquement les gérants dès qu'un stock passe sous son seuil de sécurité.",
            "trigger_type": TriggerType.STOCK_BELOW_THRESHOLD,
            "action_type": ActionType.CREATE_NOTIFICATION,
            "is_active": True
        }
    )

    # 10. Audit Logs initiaux de traçabilité
    from apps.audit.models import AuditLog
    if AuditLog.objects.filter(company=company).count() == 0:
        sample_logs = [
            {
                'action': 'LOGIN_SUCCESS',
                'resource_type': 'Authentication',
                'resource_id': str(admin_user.id),
                'user': admin_user,
                'ip_address': '192.168.1.10',
                'details': {'email': admin_user.email, 'role': admin_user.role, 'client': 'NEXORA Enterprise Desktop'}
            },
            {
                'action': 'POST_SALES',
                'resource_type': 'Sale',
                'resource_id': 'VNT-INITIAL-OUAGA',
                'user': cashier_user,
                'ip_address': '192.168.1.25',
                'details': {'total': '465000 FCFA', 'customer': cust1.name, 'method': 'MOBILE_MONEY'}
            },
            {
                'action': 'POST_PRODUCTS',
                'resource_type': 'Product',
                'resource_id': prod1.sku,
                'user': admin_user,
                'ip_address': '192.168.1.10',
                'details': {'name': prod1.name, 'price': f"{prod1.selling_price} FCFA", 'action': 'CATALOG_INIT'}
            },
            {
                'action': 'POST_INVENTORY',
                'resource_type': 'StockMovement',
                'resource_id': 'INIT-FASO',
                'user': admin_user,
                'ip_address': '192.168.1.10',
                'details': {'movement_type': 'INITIAL', 'store': store.name}
            },
            {
                'action': 'LOGIN_SUCCESS',
                'resource_type': 'Authentication',
                'resource_id': str(cashier_user.id),
                'user': cashier_user,
                'ip_address': '192.168.1.25',
                'details': {'email': cashier_user.email, 'role': cashier_user.role, 'terminal': register.name}
            },
            {
                'action': 'PERMISSION_DENIED_ATTEMPT',
                'resource_type': 'SecurityAlert',
                'resource_id': '/api/v1/settings/companies/',
                'user': cashier_user,
                'ip_address': '192.168.1.25',
                'details': {'status_code': 403, 'attempted_action': 'ACCESS_ADMIN_SETTINGS'}
            }
        ]
        for log_item in sample_logs:
            AuditLog.objects.create(
                company=company,
                action=log_item['action'],
                resource_type=log_item['resource_type'],
                resource_id=log_item['resource_id'],
                user=log_item['user'],
                ip_address=log_item['ip_address'],
                details=log_item['details']
            )

    print("Seed: Données Burkina Faso (FCFA) initialisées avec succès !")

if __name__ == '__main__':
    seed_demo_data()
