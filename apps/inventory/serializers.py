from rest_framework import serializers
from .models import Store, StockLevel, StockMovement, Inventory, InventoryLine


class StoreSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = ['id', 'company', 'name', 'code', 'address', 'phone', 'manager', 'manager_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'company', 'created_at']

    def get_manager_name(self, obj):
        if obj.manager:
            return f"{obj.manager.first_name} {obj.manager.last_name} ({obj.manager.email})"
        return None


class StockLevelSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = StockLevel
        fields = ['id', 'company', 'store', 'store_name', 'product', 'product_name', 'product_sku', 'quantity']
        read_only_fields = ['id', 'company', 'quantity']


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'company', 'store', 'store_name', 'product', 'product_name', 'product_sku',
            'movement_type', 'movement_type_display', 'quantity', 'quantity_before', 'quantity_after',
            'unit_cost', 'reference', 'reason', 'user_email', 'created_at'
        ]
        read_only_fields = [
            'id', 'company', 'quantity_before', 'quantity_after', 'created_at'
        ]


class InventoryLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = InventoryLine
        fields = ['id', 'inventory', 'product', 'product_name', 'product_sku', 'expected_quantity', 'counted_quantity', 'difference', 'notes']
        read_only_fields = ['id', 'difference']


class InventorySerializer(serializers.ModelSerializer):
    lines = InventoryLineSerializer(many=True, read_only=True)
    store = serializers.PrimaryKeyRelatedField(queryset=Store.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Inventory
        fields = ['id', 'company', 'store', 'reference', 'inventory_type', 'status', 'notes', 'validated_at', 'created_by', 'lines', 'created_at']
        read_only_fields = ['id', 'company', 'status', 'validated_at', 'created_by', 'created_at']
