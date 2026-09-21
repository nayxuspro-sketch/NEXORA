from rest_framework import serializers
from .models import Sale, SaleItem, Payment, SaleReturn, SaleReturnItem


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'tax_rate', 'discount_rate', 'total']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'company', 'sale', 'purchase', 'partner', 'register', 'amount', 'payment_method', 'reference', 'created_at']
        read_only_fields = ['id', 'company', 'created_at']


class SaleReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = SaleReturnItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'refund_total']


class SaleReturnSerializer(serializers.ModelSerializer):
    items = SaleReturnItemSerializer(many=True, read_only=True)

    class Meta:
        model = SaleReturn
        fields = ['id', 'company', 'sale', 'reference', 'reason', 'refund_amount', 'items', 'created_at']
        read_only_fields = ['id', 'company', 'created_at']


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    seller_name = serializers.CharField(source='seller.email', read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'company', 'reference', 'store', 'store_name', 'register',
            'customer', 'customer_name', 'seller', 'seller_name',
            'status', 'payment_status', 'subtotal_amount', 'tax_amount',
            'discount_amount', 'total_amount', 'paid_amount', 'notes',
            'items', 'payments', 'created_at'
        ]
        read_only_fields = [
            'id', 'company', 'reference', 'status', 'payment_status',
            'subtotal_amount', 'tax_amount', 'total_amount', 'paid_amount', 'created_at'
        ]


class SaleCreateItemInputSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    discount_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)


class SaleCreateInputSerializer(serializers.Serializer):
    store = serializers.UUIDField()
    register = serializers.UUIDField(required=False, allow_null=True)
    customer = serializers.UUIDField(required=False, allow_null=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0.0)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    items = SaleCreateItemInputSerializer(many=True)
    payment = serializers.DictField(required=False, allow_null=True)
