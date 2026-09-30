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

# Store
store, _ = Store.objects.get_or_create(
    company=company,
    code="MAG-01",
    defaults={'name': "Magasin Principal Ouagadougou", 'address': "Avenue Kwamé N'Krumah, Ouagadougou"}
)

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
customer, _ = Partner.objects.update_or_create(
    company=company,
    name='Client Général Comptoir',
    defaults={
        'partner_type': 'CUSTOMER',
        'email': 'client.comptoir@nexora.bf',
        'phone': '+226 70 00 00 01',
        'address': 'Ouagadougou',
        'is_active': True,
    }
)

# Sales
now = timezone.now()
p1 = Product.objects.get(sku='LAPTOP-HP-01')
p2 = Product.objects.get(sku='MOUSE-WL-01')

s1, _ = Sale.objects.get_or_create(
    company=company,
    reference='VNT-2026-0001',
    defaults={
        'store': store,
        'register': register,
        'customer': customer,
        'seller': admin,
        'status': 'COMPLETED',
        'payment_status': 'PAID',
        'subtotal_amount': Decimal('480000.00'),
        'tax_amount': Decimal('86400.00'),
        'discount_amount': Decimal('0.00'),
        'total_amount': Decimal('566400.00'),
        'paid_amount': Decimal('566400.00'),
    }
)
SaleItem.objects.filter(sale=s1).delete()
SaleItem.objects.create(company=company, sale=s1, product=p1, quantity=Decimal('1.00'), unit_price=p1.selling_price, tax_rate=p1.tax_rate, discount_rate=Decimal('0.00'), total=p1.selling_price)
SaleItem.objects.create(company=company, sale=s1, product=p2, quantity=Decimal('2.00'), unit_price=p2.selling_price, tax_rate=p2.tax_rate, discount_rate=Decimal('0.00'), total=p2.selling_price * 2)

Payment.objects.filter(sale=s1).delete()
Payment.objects.create(company=company, sale=s1, register=register, payment_method='CASH', amount=Decimal('566400.00'), reference='PAY-VNT-0001', processed_by=admin)

print("Base de données initialisée avec succès !")
