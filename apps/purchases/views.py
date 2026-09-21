from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets import TenantModelViewSet
from apps.catalog.models import Product
from apps.inventory.models import Store
from apps.partners.models import Partner
from .models import Purchase, PurchaseReturn
from .serializers import (
    PurchaseSerializer,
    PurchaseCreateInputSerializer,
    PurchaseReturnSerializer
)
from .services import PurchaseService


class PurchaseViewSet(TenantModelViewSet):
    queryset = Purchase.objects.select_related('supplier', 'store', 'purchaser').prefetch_related('items__product').all()
    serializer_class = PurchaseSerializer
    filterset_fields = ['supplier', 'store', 'status', 'payment_status']
    search_fields = ['reference', 'supplier__name']
    ordering_fields = ['created_at', 'total_amount']

    def create(self, request, *args, **kwargs):
        input_serializer = PurchaseCreateInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        user = request.user
        company = user.company

        try:
            supplier = Partner.objects.get(id=data['supplier'], company=company)
            store = Store.objects.get(id=data['store'], company=company)
        except (Partner.DoesNotExist, Store.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        items_data = []
        for item_in in data['items']:
            try:
                prod = Product.objects.get(id=item_in['product'], company=company)
            except Product.DoesNotExist:
                return Response({'error': f"Produit {item_in['product']} introuvable"}, status=status.HTTP_400_BAD_REQUEST)
            items_data.append({
                'product': prod,
                'quantity': item_in['quantity'],
                'unit_cost': item_in.get('unit_cost', prod.cost_price),
                'tax_rate': item_in.get('tax_rate', prod.tax_rate)
            })

        try:
            purchase = PurchaseService.create_purchase(
                company=company,
                supplier=supplier,
                store=store,
                items_data=items_data,
                purchaser=user,
                notes=data.get('notes', ''),
                auto_receive=data.get('auto_receive', False)
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PurchaseSerializer(purchase).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        purchase = self.get_object()
        try:
            received = PurchaseService.receive_purchase(purchase, user=request.user)
            return Response(PurchaseSerializer(received).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        purchase = self.get_object()
        amount = request.data.get('amount')
        method = request.data.get('method', 'BANK_TRANSFER')
        ref = request.data.get('reference', '')

        if not amount:
            return Response({'error': 'Le montant est obligatoire'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = PurchaseService.process_payment(
                company=purchase.company,
                purchase=purchase,
                amount=amount,
                method=method,
                user=request.user,
                reference=ref
            )
            return Response({'status': 'Paiement effectué', 'paid_amount': str(purchase.paid_amount)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        purchase = self.get_object()
        reason = request.data.get('reason', '')
        try:
            cancelled = PurchaseService.cancel_purchase(purchase, user=request.user, reason=reason)
            return Response(PurchaseSerializer(cancelled).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def return_items(self, request, pk=None):
        purchase = self.get_object()
        items_payload = request.data.get('items', [])
        reason = request.data.get('reason', '')

        if not items_payload:
            return Response({'error': 'Veuillez spécifier les articles à retourner'}, status=status.HTTP_400_BAD_REQUEST)

        return_items = []
        for item_in in items_payload:
            try:
                prod = Product.objects.get(id=item_in['product'], company=purchase.company)
            except Product.DoesNotExist:
                return Response({'error': f"Produit {item_in['product']} introuvable"}, status=status.HTTP_400_BAD_REQUEST)
            return_items.append({
                'product': prod,
                'quantity': item_in['quantity'],
                'unit_cost': item_in.get('unit_cost', prod.cost_price)
            })

        try:
            ret = PurchaseService.process_return(
                purchase=purchase,
                return_items=return_items,
                user=request.user,
                reason=reason
            )
            return Response(PurchaseReturnSerializer(ret).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseReturnViewSet(TenantModelViewSet):
    queryset = PurchaseReturn.objects.prefetch_related('items__product').all()
    serializer_class = PurchaseReturnSerializer
    filterset_fields = ['purchase']
