import os
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.companies.models import Company
from apps.inventory.models import Store, StockLevel
from apps.catalog.models import Product, Category, Unit
from apps.pos.models import CashRegister
from apps.partners.models import Partner
from apps.sales.models import Sale, SaleItem, Payment
from django.contrib.auth import get_user_model

User = get_user_model()

# Company
company, _ = Company.objects.get_or_create(
    slug="nexora-bf",
    defaults={'name': "NEXORA ENTERPRISE BF", 'currency': 'XOF', 'phone': '+226 25 00 00 00', 'email': 'contact@nexora.bf'}
)

# Admin user
if not User.objects.filter(email='admin@nexora.bf').exists():
    admin = User.objects.create_superuser(email='admin@nexora.bf', password='admin123', company=company)
else:
    admin = User.objects.get(email='admin@nexora.bf')

# Groupes / Profils par defaut
from django.contrib.auth.models import Group, Permission
admin_group, _ = Group.objects.get_or_create(name="Direction & Administration Générale")
admin_group.permissions.set(Permission.objects.filter(content_type__app_label__in=['accounts', 'sales', 'inventory', 'purchases', 'pos', 'audit', 'companies', 'catalog', 'partners']))
admin.groups.add(admin_group)

manager_group, _ = Group.objects.get_or_create(name="Responsable Magasin & Stocks")
manager_group.permissions.set(Permission.objects.filter(content_type__app_label__in=['inventory', 'catalog', 'purchases', 'partners']))

cashier_group, _ = Group.objects.get_or_create(name="Caissier & Vendeur Comptoir")
cashier_group.permissions.set(Permission.objects.filter(
    content_type__app_label__in=['pos', 'sales', 'catalog', 'partners', 'inventory'],
    codename__in=[
        # Caisse & Ventes
        'add_sale', 'view_sale', 'change_sale',
        'add_saleitem', 'view_saleitem',
        'add_payment', 'view_payment',
        'view_cashregister', 'view_registersession',
        # Catalogue & Produits (Consultation obligatoire pour la caisse)
        'view_product', 'view_category', 'view_unit',
        # Clients (Consultation et sélection pour facturation)
        'view_partner', 'add_partner',
        # Consultation des disponibilités de stock
        'view_stocklevel', 'view_store'
    ]
))

auditor_group, _ = Group.objects.get_or_create(name="Auditeur & Contrôleur Financier")
auditor_group.permissions.set(Permission.objects.filter(content_type__app_label__in=['audit', 'sales', 'pos', 'inventory', 'catalog', 'partners'], codename__startswith='view_'))

accountant_group, _ = Group.objects.get_or_create(name="Comptabilité & Finances")
accountant_group.permissions.set(Permission.objects.filter(
    content_type__app_label__in=['sales', 'pos', 'partners', 'audit', 'purchases'],
    codename__in=['view_sale', 'view_payment', 'view_partner', 'view_auditlog', 'view_cashregister', 'view_product', 'change_payment']
))

# Store
store, _ = Store.objects.get_or_create(
    company=company,
    code="MAG-01",
    defaults={'name': "Magasin Principal Ouagadougou", 'address': "Avenue Kwamé N'Krumah, Ouagadougou"}
)

# Utilisateurs types avec leurs rôles et profils associés
default_profiles = [
    ('caissier@nexora-bf.com', 'Amadou', 'Ouédraogo', 'CASHIER', cashier_group, 'Cashier123!'),
    ('caissier@nexora.bf', 'Amadou', 'Ouédraogo', 'CASHIER', cashier_group, 'Cashier123!'),
    ('manager@nexora.bf', 'Ousmane', 'Sawadogo', 'MANAGER', manager_group, 'Manager123!'),
    ('stock@nexora.bf', 'Fatou', 'Kaboré', 'STOCK_KEEPER', manager_group, 'Stock123!'),
    ('comptable@nexora.bf', 'Issa', 'Traoré', 'ACCOUNTANT', accountant_group, 'Compta123!'),
    ('auditeur@nexora.bf', 'Boureima', 'Sankara', 'AUDITOR', auditor_group, 'Audit123!'),
]

for email, fn, ln, role, grp, pwd in default_profiles:
    u, _ = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': fn,
            'last_name': ln,
            'role': role,
            'company': company,
            'is_staff': False,
            'is_superuser': False,
            'is_active': True,
        }
    )
    u.role = role
    u.company = company
    u.set_password(pwd)
    u.save()
    u.groups.clear()
    u.groups.add(grp)

# Cash Register
register, _ = CashRegister.objects.get_or_create(
    company=company,
    store=store,
    code="REG-01",
    defaults={'name': "Caisse Principale 01", 'current_balance': 150000.00}
)

# Category & Unit
cat_info, _ = Category.objects.get_or_create(company=company, slug="informatique", defaults={'name': "Informatique & High-Tech"})
cat_bur, _ = Category.objects.get_or_create(company=company, slug="bureautique", defaults={'name': "Fournitures de Bureau"})
cat_alim, _ = Category.objects.get_or_create(company=company, slug="alimentation", defaults={'name': "Alimentation & Boissons"})

unit_pcs, _ = Unit.objects.get_or_create(company=company, symbol="pcs", defaults={'name': "Pièce"})
unit_box, _ = Unit.objects.get_or_create(company=company, symbol="bte", defaults={'name': "Boîte"})

# Products
sample_products = [
    {
        'sku': 'LAPTOP-HP-01',
        'name': 'Ordinateur Portable HP ProBook 15 G9',
        'barcode': '3700123456789',
        'description': 'Intel Core i5 12e Gén, 16 Go RAM, 512 Go SSD NVMe',
        'cost_price': 325000.00,
        'selling_price': 450000.00,
        'category': cat_info,
        'unit': unit_pcs,
        'alert_threshold': 5,
        'stock': 18
    },
    {
        'sku': 'MOUSE-WL-01',
        'name': 'Souris Sans Fil Ergonomique Rechargeable',
        'barcode': '3700123456790',
        'description': 'Capteur laser 2.4GHz + Bluetooth, 4000 DPI',
        'cost_price': 8000.00,
        'selling_price': 15000.00,
        'category': cat_info,
        'unit': unit_pcs,
        'alert_threshold': 10,
        'stock': 45
    },
    {
        'sku': 'KEYB-USB-01',
        'name': 'Clavier USB Filaire AZERTY Confort',
        'barcode': '3700123456791',
        'description': 'Clavier bureautique anti-éclaboussures',
        'cost_price': 6500.00,
        'selling_price': 12500.00,
        'category': cat_info,
        'unit': unit_pcs,
        'alert_threshold': 8,
        'stock': 32
    },
    {
        'sku': 'RAMETTE-A4-DOUBLEA',
        'name': 'Ramette Papier Double A 80g A4 (500 feuilles)',
        'barcode': '3700123456793',
        'description': 'Papier haute blancheur pour imprimante',
        'cost_price': 2800.00,
        'selling_price': 4000.00,
        'category': cat_bur,
        'unit': unit_box,
        'alert_threshold': 20,
        'stock': 120
    }
]

for sp in sample_products:
    stock_qty = sp.pop('stock')
    sku = sp['sku']
    prod, _ = Product.objects.update_or_create(company=company, sku=sku, defaults=sp)
    StockLevel.objects.update_or_create(company=company, store=store, product=prod, defaults={'quantity': stock_qty})

# Partners
cust1, _ = Partner.objects.update_or_create(
    company=company,
    name='Client Général Comptoir',
    defaults={'partner_type': 'CUSTOMER', 'phone': '+226 70 00 00 01', 'address': 'Ouagadougou', 'is_active': True}
)
cust2, _ = Partner.objects.update_or_create(
    company=company,
    name='Société Faso Technologies SARL',
    defaults={'partner_type': 'CUSTOMER', 'phone': '+226 25 30 11 22', 'address': 'Avenue Kwamé N’Krumah', 'is_active': True}
)
cust3, _ = Partner.objects.update_or_create(
    company=company,
    name='Cabinet Audit & Conseils Ouaga',
    defaults={'partner_type': 'CUSTOMER', 'phone': '+226 25 36 45 50', 'address': 'Koulouba', 'is_active': True}
)

# Sales transactions
now = timezone.now()
p1 = Product.objects.get(sku='LAPTOP-HP-01')
p2 = Product.objects.get(sku='MOUSE-WL-01')
p3 = Product.objects.get(sku='KEYB-USB-01')
p4 = Product.objects.get(sku='RAMETTE-A4-DOUBLEA')

transactions = [
    {
        'ref': 'FAC-2026-0001',
        'customer': cust1,
        'days_ago': 0,
        'hours_ago': 1,
        'pay_method': 'CASH',
        'items': [(p1, Decimal('1.00')), (p2, Decimal('2.00'))],
    },
    {
        'ref': 'FAC-2026-0002',
        'customer': cust2,
        'days_ago': 0,
        'hours_ago': 3,
        'pay_method': 'MOBILE_MONEY',
        'items': [(p3, Decimal('2.00')), (p4, Decimal('5.00'))],
    },
    {
        'ref': 'FAC-2026-0003',
        'customer': cust3,
        'days_ago': 1,
        'hours_ago': 2,
        'pay_method': 'CARD',
        'items': [(p2, Decimal('3.00')), (p3, Decimal('1.00'))],
    },
    {
        'ref': 'FAC-2026-0004',
        'customer': cust1,
        'days_ago': 2,
        'hours_ago': 4,
        'pay_method': 'CASH',
        'items': [(p1, Decimal('2.00'))],
    },
    {
        'ref': 'FAC-2026-0005',
        'customer': cust2,
        'days_ago': 3,
        'hours_ago': 5,
        'pay_method': 'MOBILE_MONEY',
        'items': [(p4, Decimal('10.00')), (p2, Decimal('2.00'))],
    },
    {
        'ref': 'FAC-2026-0006',
        'customer': cust3,
        'days_ago': 5,
        'hours_ago': 6,
        'pay_method': 'CASH',
        'items': [(p3, Decimal('4.00')), (p1, Decimal('1.00'))],
    },
    {
        'ref': 'FAC-2026-0007',
        'customer': cust1,
        'days_ago': 8,
        'hours_ago': 2,
        'pay_method': 'CASH',
        'items': [(p2, Decimal('5.00')), (p4, Decimal('8.00'))],
    },
]

for t in transactions:
    created_time = now - timedelta(days=t['days_ago'], hours=t['hours_ago'])
    subtotal = sum((prod.selling_price * qty for prod, qty in t['items']), Decimal('0.00'))
    tax = (subtotal * Decimal('18.00')) / Decimal('100.00')
    total = subtotal + tax

    sale, _ = Sale.objects.update_or_create(
        company=company,
        reference=t['ref'],
        defaults={
            'store': store,
            'register': register,
            'customer': t['customer'],
            'seller': admin,
            'status': 'COMPLETED',
            'payment_status': 'PAID',
            'subtotal_amount': subtotal,
            'tax_amount': tax,
            'discount_amount': Decimal('0.00'),
            'total_amount': total,
            'paid_amount': total,
        }
    )
    Sale.objects.filter(id=sale.id).update(created_at=created_time)

    SaleItem.objects.filter(sale=sale).delete()
    for prod, qty in t['items']:
        line_tot = prod.selling_price * qty
        SaleItem.objects.create(
            company=company,
            sale=sale,
            product=prod,
            quantity=qty,
            unit_price=prod.selling_price,
            tax_rate=Decimal('18.00'),
            discount_rate=Decimal('0.00'),
            total=line_tot
        )

    Payment.objects.filter(sale=sale).delete()
    Payment.objects.create(
        company=company,
        sale=sale,
        register=register,
        payment_method=t['pay_method'],
        amount=total,
        reference=f"PAY-{t['ref']}",
        processed_by=admin
    )
    Payment.objects.filter(sale=sale).update(created_at=created_time)

print("Base de données initialisée avec 7 transactions complètes pour le vendeur !")
