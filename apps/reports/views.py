from decimal import Decimal
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.common.permissions import IsAuthenticatedAndInTenant
from apps.sales.models import Sale, SaleStatus, Payment
from apps.purchases.models import Purchase, PurchaseStatus
from apps.inventory.models import StockLevel, StockMovement
from apps.catalog.models import Product


class DashboardReportSerializer(serializers.Serializer):
    period_days = serializers.IntegerField()
    sales = serializers.DictField()
    purchases = serializers.DictField()
    profitability = serializers.DictField()
    inventory = serializers.DictField()


class InventoryValuationReportSerializer(serializers.Serializer):
    total_cost_valuation = serializers.CharField()
    total_retail_valuation = serializers.CharField()
    potential_margin = serializers.CharField()
    items_count = serializers.IntegerField()
    items = serializers.ListField()


class DashboardSummaryReportView(APIView):
    """
    Business Intelligence & KPI Dashboard Endpoint
    Compréhension → Anticipation
    """
    permission_classes = [IsAuthenticatedAndInTenant]

    @extend_schema(
        responses={200: DashboardReportSerializer},
        parameters=[
            OpenApiParameter(name='days', description='Nombre de jours pour l\'analyse (défaut 30)', required=False, type=int)
        ]
    )
    def get(self, request):
        company = request.user.company

        # Period filter (default 30 days)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        # Sales KPIs
        sales_qs = Sale.objects.filter(company=company, status=SaleStatus.COMPLETED, created_at__gte=start_date)
        sales_aggregate = sales_qs.aggregate(
            total_sales=Sum('total_amount'),
            sales_count=Count('id'),
            total_tax=Sum('tax_amount'),
            total_discount=Sum('discount_amount')
        )

        # Purchases KPIs
        purchases_qs = Purchase.objects.filter(company=company, status=PurchaseStatus.RECEIVED, created_at__gte=start_date)
        purchases_aggregate = purchases_qs.aggregate(
            total_purchases=Sum('total_amount'),
            purchases_count=Count('id')
        )

        # Stock valuation
        stock_qs = StockLevel.objects.filter(company=company)
        total_items_in_stock = stock_qs.aggregate(total_qty=Sum('quantity'))['total_qty'] or Decimal('0.00')

        # Stock low alerts
        low_stock_products = []
        for level in stock_qs.select_related('product', 'store').filter(quantity__lte=F('product__alert_threshold')):
            low_stock_products.append({
                'product_id': str(level.product.id),
                'product_name': level.product.name,
                'sku': level.product.sku,
                'store_name': level.store.name,
                'current_stock': str(level.quantity),
                'alert_threshold': str(level.product.alert_threshold)
            })

        # Net estimated margin
        total_sales = sales_aggregate['total_sales'] or Decimal('0.00')
        total_purchases = purchases_aggregate['total_purchases'] or Decimal('0.00')
        gross_margin = total_sales - total_purchases

        return Response({
            'period_days': days,
            'sales': {
                'total_amount': str(total_sales),
                'count': sales_aggregate['sales_count'] or 0,
                'tax_collected': str(sales_aggregate['total_tax'] or Decimal('0.00')),
                'discounts_granted': str(sales_aggregate['total_discount'] or Decimal('0.00')),
            },
            'purchases': {
                'total_amount': str(total_purchases),
                'count': purchases_aggregate['purchases_count'] or 0,
            },
            'profitability': {
                'gross_estimate': str(gross_margin),
            },
            'inventory': {
                'total_units_stocked': str(total_items_in_stock),
                'low_stock_alerts_count': len(low_stock_products),
                'low_stock_items': low_stock_products[:10]
            }
        })


class InventoryValuationReportView(APIView):
    """
    Inventory valuation report based on current stock levels and cost prices.
    """
    permission_classes = [IsAuthenticatedAndInTenant]

    @extend_schema(responses={200: InventoryValuationReportSerializer})
    def get(self, request):
        company = request.user.company
        levels = StockLevel.objects.filter(company=company).select_related('product', 'store')

        total_cost_valuation = Decimal('0.00')
        total_selling_valuation = Decimal('0.00')
        breakdown = []

        for lvl in levels:
            cost_val = lvl.quantity * lvl.product.cost_price
            sell_val = lvl.quantity * lvl.product.selling_price
            total_cost_valuation += cost_val
            total_selling_valuation += sell_val

            breakdown.append({
                'store': lvl.store.name,
                'product': lvl.product.name,
                'sku': lvl.product.sku,
                'quantity': str(lvl.quantity),
                'unit_cost': str(lvl.product.cost_price),
                'unit_price': str(lvl.product.selling_price),
                'total_cost_value': str(cost_val),
                'total_retail_value': str(sell_val),
            })

        return Response({
            'total_cost_valuation': str(total_cost_valuation),
            'total_retail_valuation': str(total_selling_valuation),
            'potential_margin': str(total_selling_valuation - total_cost_valuation),
            'items_count': len(breakdown),
            'items': breakdown
        })
