from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.permissions import IsAuthenticatedAndInTenant
from apps.catalog.models import Product
from apps.inventory.models import StockLevel, StockMovement, StockMovementType, Store


class StockIntelligenceAnalyticsView(APIView):
    """
    Intelligent Stock Analysis & Anticipation Engine:
    - Ruptures & critical thresholds
    - Fast moving vs slow moving / dormant items (rotation)
    - Loss & damage anomalies
    - Predictive consumption & estimated replenishment needs (Forecasting note: estimations)
    """
    permission_classes = [IsAuthenticatedAndInTenant]

    def get(self, request):
        company = getattr(request.user, 'company', None)
        if not company:
            from apps.companies.models import Company
            company = Company.objects.first()

        store_id = request.query_params.get('store_id')
        days = int(request.query_params.get('days', 30))
        since_date = timezone.now() - timedelta(days=days)

        # Base filters
        levels_qs = StockLevel.objects.filter(company=company).select_related('product', 'store')
        movements_qs = StockMovement.objects.filter(company=company, created_at__gte=since_date)

        if store_id:
            levels_qs = levels_qs.filter(store_id=store_id)
            movements_qs = movements_qs.filter(store_id=store_id)

        # 1. Ruptures & Critical Alerts
        out_of_stock = []
        critical_alerts = []
        for level in levels_qs:
            threshold = level.product.alert_threshold
            qty = level.quantity
            item_data = {
                'product_id': str(level.product.id),
                'product_name': level.product.name,
                'sku': level.product.sku,
                'store_name': level.store.name,
                'current_stock': str(qty),
                'alert_threshold': str(threshold),
                'unit_cost': str(level.product.cost_price),
            }
            if qty <= Decimal('0.00'):
                out_of_stock.append(item_data)
            elif qty <= threshold:
                critical_alerts.append(item_data)

        # 2. Consumption & Velocity (Fast vs Slow vs Dormant)
        sales_movements = movements_qs.filter(movement_type=StockMovementType.SALE)
        consumption_by_product = (
            sales_movements.values('product')
            .annotate(total_consumed=Sum('quantity')) # quantity is negative for SALE
        )

        consumed_dict = {item['product']: abs(item['total_consumed'] or Decimal('0.00')) for item in consumption_by_product}

        fast_moving = []
        slow_moving = []
        dormant_items = []
        replenishment_forecasts = []

        all_products = Product.objects.filter(company=company, is_active=True)

        for prod in all_products:
            consumed = consumed_dict.get(prod.id, Decimal('0.00'))
            avg_daily_consumption = (consumed / Decimal(str(days))).quantize(Decimal('0.01'))

            # Total current stock for this product across company/store
            total_current_qty = levels_qs.filter(product=prod).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')

            # Days of remaining inventory estimate
            if avg_daily_consumption > Decimal('0.00'):
                days_of_stock_left = int(total_current_qty / avg_daily_consumption) if total_current_qty > 0 else 0
            else:
                days_of_stock_left = 999 if total_current_qty > 0 else 0

            # Classification
            summary = {
                'product_id': str(prod.id),
                'name': prod.name,
                'sku': prod.sku,
                'units_sold': str(consumed),
                'avg_daily_consumption': str(avg_daily_consumption),
                'current_stock': str(total_current_qty),
                'days_of_stock_left': days_of_stock_left,
            }

            if consumed >= Decimal('10.00'):
                fast_moving.append(summary)
            elif consumed > Decimal('0.00'):
                slow_moving.append(summary)
            elif total_current_qty > Decimal('0.00'):
                dormant_items.append(summary)

            # Replenishment forecasting (Target: 30 days buffer)
            if avg_daily_consumption > Decimal('0.00'):
                target_stock = avg_daily_consumption * Decimal('30')
                if total_current_qty < target_stock:
                    suggested_order = (target_stock - total_current_qty).quantize(Decimal('1.00'))
                    replenishment_forecasts.append({
                        'product_id': str(prod.id),
                        'product_name': prod.name,
                        'sku': prod.sku,
                        'current_stock': str(total_current_qty),
                        'avg_daily_consumption': str(avg_daily_consumption),
                        'estimated_days_left': days_of_stock_left,
                        'suggested_reorder_qty': str(suggested_order),
                        'estimated_cost': str((suggested_order * prod.cost_price).quantize(Decimal('0.01'))),
                        'priority': 'URGENT' if days_of_stock_left <= 7 else 'NORMAL',
                        'disclaimer': 'Estimation prévisionnelle basée sur la consommation moyenne des 30 derniers jours.'
                    })

        # 3. Anomalies (Losses and Damages)
        loss_damage_moves = movements_qs.filter(
            Q(movement_type=StockMovementType.LOSS) | Q(movement_type=StockMovementType.DAMAGE)
        ).select_related('product', 'store')

        anomalies = []
        for mv in loss_damage_moves[:20]:
            anomalies.append({
                'id': str(mv.id),
                'product_name': mv.product.name,
                'sku': mv.product.sku,
                'store': mv.store.name,
                'movement_type': mv.get_movement_type_display(),
                'quantity': str(abs(mv.quantity)),
                'reason': mv.reason,
                'reference': mv.reference,
                'date': mv.created_at.isoformat()
            })

        return Response({
            'status': 'success',
            'period_days': days,
            'summary': {
                'out_of_stock_count': len(out_of_stock),
                'critical_alerts_count': len(critical_alerts),
                'dormant_count': len(dormant_items),
                'fast_moving_count': len(fast_moving),
                'reorder_suggestions_count': len(replenishment_forecasts),
                'anomalies_count': len(anomalies),
            },
            'out_of_stock': out_of_stock,
            'critical_alerts': critical_alerts,
            'fast_moving': sorted(fast_moving, key=lambda x: float(x['units_sold']), reverse=True)[:10],
            'slow_moving': slow_moving[:10],
            'dormant_items': dormant_items[:10],
            'replenishment_forecasts': sorted(replenishment_forecasts, key=lambda x: x['estimated_days_left'])[:15],
            'anomalies': anomalies,
            'predictive_notice': 'Toutes les prévisions et suggestions de réapprovisionnement constituent des estimations indicatives calculées sur la base de l\'historique des ventes.'
        })
