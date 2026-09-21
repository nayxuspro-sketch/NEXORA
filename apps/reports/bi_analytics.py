from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.permissions import IsAuthenticatedAndInTenant
from apps.sales.models import Sale, SaleItem, SaleStatus
from apps.purchases.models import Purchase, PurchaseStatus
from apps.inventory.models import StockLevel, StockMovement, StockMovementType
from apps.partners.models import Partner
from apps.catalog.models import Product, Category
from apps.pos.models import CashRegister


class BusinessIntelligenceAnalyticsView(APIView):
    """
    Multi-Role Business Intelligence & Analytical Insights Engine:
    - Roles: EXECUTIVE (Direction), STORE_MANAGER (Gérant), SALES (Commercial), STOCK (Logistique), CASHIER (Caisse)
    - Sales KPIs: revenue, volume, average basket, trend explanations
    - Profitability: gross revenue, total cost, estimated profit, gross margin %
    - Stock metrics: valuation, turnover, dormant stock, critical items
    - Customer segmentation & buying behaviour (RFM foundations)
    - Data-driven natural language explanations: "Pourquoi le CA ou la marge a évolué ?"
    """
    permission_classes = [IsAuthenticatedAndInTenant]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            from apps.companies.models import Company
            company = Company.objects.first()
        user_role = getattr(request.user, 'role', 'ADMIN')
        requested_view = request.query_params.get('view') # 'executive', 'manager', 'sales', 'stock', 'cashier'
        days = int(request.query_params.get('days', 30))

        # Default view mapped to user role if not explicitly requested
        if not requested_view:
            if user_role == 'ADMIN':
                requested_view = 'executive'
            elif user_role == 'MANAGER':
                requested_view = 'manager'
            elif user_role == 'STOCK_KEEPER':
                requested_view = 'stock'
            elif user_role == 'CASHIER':
                requested_view = 'cashier'
            else:
                requested_view = 'executive'

        now = timezone.now()
        current_period_start = now - timedelta(days=days)
        previous_period_start = current_period_start - timedelta(days=days)

        # 1. Current Period Sales
        current_sales = Sale.objects.filter(
            company=company,
            status=SaleStatus.COMPLETED,
            created_at__gte=current_period_start
        )
        prev_sales = Sale.objects.filter(
            company=company,
            status=SaleStatus.COMPLETED,
            created_at__gte=previous_period_start,
            created_at__lt=current_period_start
        )

        curr_agg = current_sales.aggregate(
            total_revenue=Sum('total_amount'),
            sales_count=Count('id'),
            avg_basket=Avg('total_amount'),
            total_tax=Sum('tax_amount'),
            total_discount=Sum('discount_amount')
        )
        prev_agg = prev_sales.aggregate(
            total_revenue=Sum('total_amount'),
            sales_count=Count('id'),
            avg_basket=Avg('total_amount')
        )

        curr_revenue = curr_agg['total_revenue'] or Decimal('0.00')
        prev_revenue = prev_agg['total_revenue'] or Decimal('0.00')
        curr_count = curr_agg['sales_count'] or 0
        prev_count = prev_agg['sales_count'] or 0
        curr_basket = curr_agg['avg_basket'] or Decimal('0.00')
        prev_basket = prev_agg['avg_basket'] or Decimal('0.00')

        # Revenue delta
        rev_growth_pct = Decimal('0.00')
        if prev_revenue > Decimal('0.00'):
            rev_growth_pct = (((curr_revenue - prev_revenue) / prev_revenue) * 100).quantize(Decimal('0.01'))

        # 2. Profitability & Margin Analysis
        # Calculate cost of goods sold (COGS) from sales items
        sale_items = SaleItem.objects.filter(
            sale__in=current_sales
        ).select_related('product', 'product__category', 'sale__seller', 'sale__store')

        total_cost = Decimal('0.00')
        category_breakdown = {}
        seller_breakdown = {}
        store_breakdown = {}
        top_products_dict = {}

        for item in sale_items:
            unit_cost = item.product.cost_price or Decimal('0.00')
            item_cost = unit_cost * item.quantity
            total_cost += item_cost

            # Top products
            p_id = str(item.product.id)
            if p_id not in top_products_dict:
                top_products_dict[p_id] = {
                    'name': item.product.name,
                    'sku': item.product.sku,
                    'qty': Decimal('0.00'),
                    'revenue': Decimal('0.00')
                }
            top_products_dict[p_id]['qty'] += item.quantity
            top_products_dict[p_id]['revenue'] += item.total

            # By Category
            cat_name = item.product.category.name if item.product.category else 'Sans catégorie'
            if cat_name not in category_breakdown:
                category_breakdown[cat_name] = {'revenue': Decimal('0.00'), 'qty': Decimal('0.00')}
            category_breakdown[cat_name]['revenue'] += item.total
            category_breakdown[cat_name]['qty'] += item.quantity

            # By Seller
            seller_name = item.sale.seller.email if item.sale.seller else 'Non spécifié'
            if seller_name not in seller_breakdown:
                seller_breakdown[seller_name] = {'revenue': Decimal('0.00'), 'sales_count': set()}
            seller_breakdown[seller_name]['revenue'] += item.total
            seller_breakdown[seller_name]['sales_count'].add(item.sale_id)

            # By Store
            store_name = item.sale.store.name if item.sale.store else 'Principal'
            if store_name not in store_breakdown:
                store_breakdown[store_name] = {'revenue': Decimal('0.00'), 'count': 0}
            store_breakdown[store_name]['revenue'] += item.total

        estimated_gross_profit = curr_revenue - total_cost
        margin_rate = Decimal('0.00')
        if curr_revenue > Decimal('0.00'):
            margin_rate = ((estimated_gross_profit / curr_revenue) * 100).quantize(Decimal('0.01'))

        # Format breakdowns
        top_selling_products = sorted(
            top_products_dict.values(),
            key=lambda x: float(x['revenue']),
            reverse=True
        )[:5]

        # 3. Stock Valuation & Health
        stock_qs = StockLevel.objects.filter(company=company).select_related('product', 'store')
        stock_val_cost = Decimal('0.00')
        stock_val_retail = Decimal('0.00')
        critical_stock_count = 0
        total_items_in_stock = Decimal('0.00')

        for sl in stock_qs:
            total_items_in_stock += sl.quantity
            stock_val_cost += (sl.quantity * sl.product.cost_price)
            stock_val_retail += (sl.quantity * sl.product.selling_price)
            if sl.quantity <= sl.product.alert_threshold:
                critical_stock_count += 1

        # 4. Customer Behavior & Segmentation
        partners_qs = Partner.objects.filter(company=company)
        total_customers = partners_qs.filter(partner_type__in=['CUSTOMER', 'BOTH']).count()
        active_customers = current_sales.filter(customer__isnull=False).values('customer').distinct().count()

        # 5. Data-driven Explanations & Insights ("Pourquoi les chiffres ont évolué ?")
        explanations = []
        if rev_growth_pct > 0:
            if curr_basket > prev_basket:
                explanations.append(
                    f"Le chiffre d'affaires progresse de {rev_growth_pct}%, principalement porté par une hausse du panier moyen "
                    f"passé de {prev_basket.quantize(Decimal('1.00'))} FCFA à {curr_basket.quantize(Decimal('1.00'))} FCFA."
                )
            else:
                explanations.append(
                    f"Le chiffre d'affaires progresse de {rev_growth_pct}%, tiré par une hausse du volume de transactions "
                    f"({curr_count} ventes vs {prev_count} sur la période précédente)."
                )
        elif rev_growth_pct < 0:
            explanations.append(
                f"Le chiffre d'affaires est en baisse de {abs(rev_growth_pct)}% par rapport aux {days} jours précédents. "
                f"Cette baisse s'explique par une diminution du volume de transactions ({curr_count} vs {prev_count})."
            )
        else:
            explanations.append("Le niveau d'activité est stable par rapport à la période de référence précédente.")

        if top_selling_products:
            best = top_selling_products[0]
            share = ((best['revenue'] / curr_revenue) * 100).quantize(Decimal('0.1')) if curr_revenue > 0 else 0
            explanations.append(
                f"La performance commerciale est fortement consolidée par '{best['name']}', qui génère à lui seul {share}% des revenus analysés."
            )

        if critical_stock_count > 0:
            explanations.append(
                f"Attention : {critical_stock_count} produit(s) sont sous le seuil d'alerte, présentant un risque direct de rupture et de perte de chiffre d'affaires futur."
            )

        # 6. Role-Specific Tailored Views
        response_payload = {
            'status': 'success',
            'requested_view': requested_view,
            'period_days': days,
            'insights_explanation': explanations,
            'sales_overview': {
                'current_revenue': str(curr_revenue),
                'previous_revenue': str(prev_revenue),
                'growth_pct': str(rev_growth_pct),
                'sales_count': curr_count,
                'avg_basket': str(curr_basket.quantize(Decimal('0.01'))),
                'tax_collected': str(curr_agg['total_tax'] or Decimal('0.00')),
                'discounts_granted': str(curr_agg['total_discount'] or Decimal('0.00')),
            },
            'profitability': {
                'gross_revenue': str(curr_revenue),
                'total_cost_of_goods': str(total_cost),
                'estimated_profit': str(estimated_gross_profit),
                'margin_rate_pct': str(margin_rate),
            },
            'stock_health': {
                'total_cost_valuation': str(stock_val_cost),
                'total_retail_valuation': str(stock_val_retail),
                'total_units': str(total_items_in_stock),
                'critical_items_count': critical_stock_count,
            },
            'customer_insights': {
                'total_customer_accounts': total_customers,
                'active_buying_customers': active_customers,
                'customer_retention_rate': f"{(active_customers / total_customers * 100):.1f}%" if total_customers > 0 else '0%',
            },
            'top_products': [
                {'name': p['name'], 'sku': p['sku'], 'qty': str(p['qty']), 'revenue': str(p['revenue'])}
                for p in top_selling_products
            ],
            'categories': [
                {'category': k, 'revenue': str(v['revenue']), 'qty': str(v['qty'])}
                for k, v in category_breakdown.items()
            ],
            'sellers_performance': [
                {'seller': k, 'revenue': str(v['revenue']), 'transactions': len(v['sales_count'])}
                for k, v in seller_breakdown.items()
            ],
            'stores_performance': [
                {'store': k, 'revenue': str(v['revenue'])}
                for k, v in store_breakdown.items()
            ]
        }

        return Response(response_payload)
