from apps.common.viewsets import TenantModelViewSet
from .models import Category, Unit, Product
from .serializers import CategorySerializer, UnitSerializer, ProductSerializer


class CategoryViewSet(TenantModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ['name', 'slug']


class UnitViewSet(TenantModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    search_fields = ['name', 'symbol']


class ProductViewSet(TenantModelViewSet):
    queryset = Product.objects.select_related('category', 'unit').all()
    serializer_class = ProductSerializer
    search_fields = ['name', 'sku', 'barcode']
    filterset_fields = ['category', 'is_active']
    ordering_fields = ['name', 'sku', 'selling_price', 'created_at']
