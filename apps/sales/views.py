from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets import TenantModelViewSet
from apps.catalog.models import Product
from apps.inventory.models import Store
from apps.partners.models import Partner
from apps.pos.models import CashRegister
from .models import Sale, SaleItem, Payment, SaleReturn
from .serializers import (
    SaleSerializer,
    SaleCreateInputSerializer,
    PaymentSerializer,
    SaleReturnSerializer
)
from .services import SaleService


class SaleViewSet(TenantModelViewSet):
    queryset = Sale.objects.select_related('store', 'customer', 'seller', 'register').prefetch_related('items__product', 'payments').all()
    serializer_class = SaleSerializer
    filterset_fields = ['store', 'status', 'payment_status', 'customer']
    search_fields = ['reference', 'customer__name']
    ordering_fields = ['created_at', 'total_amount']

    def create(self, request, *args, **kwargs):
        input_serializer = SaleCreateInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        user = request.user
        company = user.company

        # Validate store
        try:
            store = Store.objects.get(id=data['store'], company=company)
        except Store.DoesNotExist:
            return Response({'error': 'Magasin introuvable dans votre entreprise'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate register if provided
        register = None
        if data.get('register'):
            try:
                register = CashRegister.objects.get(id=data['register'], company=company)
            except CashRegister.DoesNotExist:
                return Response({'error': 'Caisse introuvable'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate customer if provided
        customer = None
        if data.get('customer'):
            try:
                customer = Partner.objects.get(id=data['customer'], company=company)
            except Partner.DoesNotExist:
                return Response({'error': 'Client introuvable'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare items data with product instances
        items_data = []
        for item_in in data['items']:
            try:
                prod = Product.objects.get(id=item_in['product'], company=company)
            except Product.DoesNotExist:
                return Response({'error': f"Produit {item_in['product']} introuvable"}, status=status.HTTP_400_BAD_REQUEST)
            items_data.append({
                'product': prod,
                'quantity': item_in['quantity'],
                'unit_price': item_in.get('unit_price', prod.selling_price),
                'tax_rate': item_in.get('tax_rate', prod.tax_rate),
                'discount_rate': item_in.get('discount_rate', 0.0)
            })

        try:
            sale = SaleService.create_and_complete_sale(
                company=company,
                store=store,
                items_data=items_data,
                seller=user,
                customer=customer,
                register=register,
                discount_amount=data.get('discount_amount', 0.0),
                notes=data.get('notes', ''),
                payment_data=data.get('payment')
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        sale = self.get_object()
        amount = request.data.get('amount')
        method = request.data.get('method', 'CASH')
        ref = request.data.get('reference', '')

        if not amount:
            return Response({'error': 'Le montant est obligatoire'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = SaleService.process_payment(
                company=sale.company,
                sale=sale,
                amount=amount,
                method=method,
                register=sale.register,
                user=request.user,
                reference=ref
            )
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        sale = self.get_object()
        reason = request.data.get('reason', '')
        try:
            cancelled_sale = SaleService.cancel_sale(sale, user=request.user, reason=reason)
            return Response(SaleSerializer(cancelled_sale).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def return_items(self, request, pk=None):
        sale = self.get_object()
        items_payload = request.data.get('items', [])
        reason = request.data.get('reason', '')

        if not items_payload:
            return Response({'error': 'Veuillez spécifier les articles à retourner'}, status=status.HTTP_400_BAD_REQUEST)

        return_items = []
        for item_in in items_payload:
            try:
                prod = Product.objects.get(id=item_in['product'], company=sale.company)
            except Product.DoesNotExist:
                return Response({'error': f"Produit {item_in['product']} introuvable"}, status=status.HTTP_400_BAD_REQUEST)
            return_items.append({
                'product': prod,
                'quantity': item_in['quantity'],
                'unit_price': item_in.get('unit_price', prod.selling_price)
            })

        try:
            ret = SaleService.process_return(
                sale=sale,
                return_items=return_items,
                user=request.user,
                reason=reason
            )
            return Response(SaleReturnSerializer(ret).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentViewSet(TenantModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filterset_fields = ['sale', 'purchase', 'payment_method']


class SaleReturnViewSet(TenantModelViewSet):
    queryset = SaleReturn.objects.prefetch_related('items__product').all()
    serializer_class = SaleReturnSerializer
    filterset_fields = ['sale']
