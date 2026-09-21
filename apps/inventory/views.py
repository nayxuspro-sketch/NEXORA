from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets import TenantModelViewSet
from .models import Store, StockLevel, StockMovement, Inventory, InventoryLine, InventoryStatus
from .serializers import (
    StoreSerializer,
    StockLevelSerializer,
    StockMovementSerializer,
    InventorySerializer,
    InventoryLineSerializer
)
from .services import StockService


class StoreViewSet(TenantModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    search_fields = ['name', 'code']


class StockLevelViewSet(TenantModelViewSet):
    queryset = StockLevel.objects.select_related('store', 'product').all()
    serializer_class = StockLevelSerializer
    filterset_fields = ['store', 'product']
    search_fields = ['product__name', 'product__sku']


class StockMovementViewSet(TenantModelViewSet):
    queryset = StockMovement.objects.select_related('store', 'product', 'user').all()
    serializer_class = StockMovementSerializer
    filterset_fields = ['store', 'product', 'movement_type']
    search_fields = ['product__name', 'product__sku', 'reference']


class InventoryViewSet(TenantModelViewSet):
    queryset = Inventory.objects.prefetch_related('lines__product').all()
    serializer_class = InventorySerializer
    filterset_fields = ['store', 'status']

    def perform_create(self, serializer):
        company_id = getattr(self.request.user, 'company_id', None)
        if not company_id:
            from apps.companies.models import Company
            c = Company.objects.first()
            company_id = c.id if c else None

        user = self.request.user if self.request.user.is_authenticated else None
        
        # If store is not provided, use default store of company
        store = serializer.validated_data.get('store')
        if not store:
            store = Store.objects.filter(company_id=company_id).first()
            serializer.save(
                company_id=company_id,
                created_by=user,
                store=store
            )
        else:
            serializer.save(
                company_id=company_id,
                created_by=user
            )

    @action(detail=True, methods=['post'])
    def add_line(self, request, pk=None):
        inventory = self.get_object()
        if inventory.status != InventoryStatus.DRAFT and inventory.status != InventoryStatus.IN_PROGRESS:
            return Response({'error': 'Inventaire non modifiable'}, status=status.HTTP_400_BAD_REQUEST)

        # Allow user to pass product_id, expected_quantity, counted_quantity
        data = request.data.copy()
        if 'product' not in data and 'product_id' in data:
            data['product'] = data['product_id']
        data['inventory'] = inventory.id

        # If expected_quantity is not passed, fetch current stock
        product_id = data.get('product')
        if 'expected_quantity' not in data or data.get('expected_quantity') is None:
            stock = StockLevel.objects.filter(store=inventory.store, product_id=product_id).first()
            data['expected_quantity'] = stock.quantity if stock else 0

        serializer = InventoryLineSerializer(data=data)
        if serializer.is_valid():
            line = serializer.save(company=inventory.company, inventory=inventory)
            return Response(InventoryLineSerializer(line).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        inventory = self.get_object()
        try:
            user = request.user if request.user.is_authenticated else None
            StockService.validate_inventory(inventory, user=user)
            return Response(InventorySerializer(inventory).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
