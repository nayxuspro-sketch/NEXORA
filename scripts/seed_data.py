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
from apps.sales.models import PaymentMethod
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
            password="Password123!",
            first_name="Directeur",
            last_name="Général",
            company=company,
            role=UserRole.ADMIN
        )
    else:
        admin_user.company = company
        admin_user.save()

    cashier_user = User.objects.filter(email="caissier@nexora-bf.com").first()
    if not cashier_user:
        cashier_user = User.objects.create_user(
            email="caissier@nexora-bf.com",
            password="Password123!",
            first_name="Ibrahim",
            last_name="Ouedraogo",
            company=company,
            role=UserRole.CASHIER
        )

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

    # 6. Stocks Setup
    for p, qty in [(prod1, Decimal('15.00')), (prod2, Decimal('40.00')), (prod3, Decimal('30.00')), (prod4, Decimal('10.00'))]:
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

    print("Seed: Données Burkina Faso (FCFA) initialisées avec succès !")

if __name__ == '__main__':
    seed_demo_data()
