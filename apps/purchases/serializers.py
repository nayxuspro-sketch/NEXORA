from rest_framework import serializers
from .models import Purchase, PurchaseItem, PurchaseReturn, PurchaseReturnItem


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_cost', 'tax_rate', 'total']


class PurchaseReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseReturnItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_cost', 'refund_total']


class PurchaseReturnSerializer(serializers.ModelSerializer):
    items = PurchaseReturnItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseReturn
        fields = ['id', 'company', 'purchase', 'reference', 'reason', 'refund_amount', 'items', 'created_at']
        read_only_fields = ['id', 'company', 'created_at']


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    purchaser_name = serializers.CharField(source='purchaser.email', read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'company', 'reference', 'supplier', 'supplier_name',
            'store', 'store_name', 'purchaser', 'purchaser_name',
            'status', 'payment_status', 'subtotal_amount', 'tax_amount',
            'total_amount', 'paid_amount', 'notes', 'items', 'created_at'
        ]
        read_only_fields = [
            'id', 'company', 'status', 'payment_status',
            'subtotal_amount', 'tax_amount', 'total_amount', 'paid_amount', 'created_at'
        ]


class PurchaseCreateItemInputSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)


class PurchaseCreateInputSerializer(serializers.Serializer):
    supplier = serializers.UUIDField()
    store = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    auto_receive = serializers.BooleanField(required=False, default=False)
    items = PurchaseCreateItemInputSerializer(many=True)
