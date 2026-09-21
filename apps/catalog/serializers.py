from rest_framework import serializers
from .models import Category, Unit, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'company', 'name', 'slug', 'description', 'parent', 'created_at', 'updated_at']
        read_only_fields = ['id', 'company', 'created_at', 'updated_at']


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'company', 'name', 'symbol', 'created_at', 'updated_at']
        read_only_fields = ['id', 'company', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_symbol = serializers.CharField(source='unit.symbol', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'company', 'name', 'sku', 'barcode', 'description',
            'category', 'category_name', 'unit', 'unit_symbol',
            'cost_price', 'selling_price', 'tax_rate', 'alert_threshold',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company', 'created_at', 'updated_at']
