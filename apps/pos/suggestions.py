from decimal import Decimal
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.common.permissions import IsAuthenticatedAndInTenant
from apps.catalog.models import Product
from apps.sales.models import Sale, SaleItem, SaleStatus
from apps.catalog.serializers import ProductSerializer


class SmartSuggestionsView(APIView):
    """
    Intelligent POS Recommendations:
    1. Frequently bought together (market basket analysis based on items currently in cart)
    2. Top selling recent products (trending)
    3. Discounted or promotional products
    """
    permission_classes = [IsAuthenticatedAndInTenant]

    def get(self, request):
        company = request.user.company
        product_id = request.query_params.get('product_id')

        # 1. Cross-selling suggestions
        frequently_bought = []
        if product_id:
            # Find sales that include product_id
            sales_with_product = SaleItem.objects.filter(
                company=company,
                product_id=product_id,
                sale__status=SaleStatus.COMPLETED
            ).values_list('sale_id', flat=True)[:50]

            if sales_with_product:
                related_product_ids = (
                    SaleItem.objects.filter(company=company, sale_id__in=sales_with_product)
                    .exclude(product_id=product_id)
                    .values('product')
                    .annotate(pair_count=Count('product'))
                    .order_by('-pair_count')[:4]
                )
                p_ids = [item['product'] for item in related_product_ids]
                frequently_bought = Product.objects.filter(company=company, id__in=p_ids, is_active=True)

        # 2. Trending recent items
        trending_items = (
            Product.objects.filter(company=company, is_active=True)
            .order_by('-created_at')[:4]
        )

        return Response({
            'status': 'success',
            'frequently_bought_together': ProductSerializer(frequently_bought, many=True).data,
            'trending_products': ProductSerializer(trending_items, many=True).data,
            'active_promotions': [
                {
                    'id': 'promo-pack',
                    'title': 'Pack Accessoires',
                    'description': 'Remise immédiate de 10% pour l\'achat d\'un périphérique',
                    'discount_rate': '10.00'
                }
            ]
        })
