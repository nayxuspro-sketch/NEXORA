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
        serializer.save(
            company_id=self.request.user.company_id,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def add_line(self, request, pk=None):
        inventory = self.get_object()
        if inventory.status != InventoryStatus.DRAFT and inventory.status != InventoryStatus.IN_PROGRESS:
            return Response({'error': 'Inventaire non modifiable'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InventoryLineSerializer(data=request.data)
        if serializer.is_valid():
            line = serializer.save(company=inventory.company, inventory=inventory)
            return Response(InventoryLineSerializer(line).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        inventory = self.get_object()
        try:
            StockService.validate_inventory(inventory, user=request.user)
            return Response(InventorySerializer(inventory).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
