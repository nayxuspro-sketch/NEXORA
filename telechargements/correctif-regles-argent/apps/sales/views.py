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

        user = request.user if request.user and request.user.is_authenticated else None
        company = self.get_company()
        if not user:
            from apps.accounts.models import User
            user = User.objects.filter(company=company).first()

        # Validate store safely
        from apps.common.validators import parse_safe_uuid
        store_val = data.get('store')
        store_uuid = parse_safe_uuid(store_val)
        store = None
        if store_uuid:
            store = Store.objects.filter(id=store_uuid, company=company).first()
        elif store_val:
            store = Store.objects.filter(company=company, code__iexact=str(store_val).strip()).first()
        if not store and store_val:
            # Un magasin a ete demande mais n'existe pas dans cette entreprise :
            # on refuse. Avant, l'application vendait silencieusement sur le
            # premier magasin de l'entreprise, ce qui laissait valider une vente
            # portant le magasin d'une autre entreprise.
            return Response({'error': 'Magasin introuvable dans votre entreprise'}, status=status.HTTP_400_BAD_REQUEST)
        if not store:
            # Aucun magasin precise : comportement d'origine (premier magasin).
            store = Store.objects.filter(company=company).first()
        if not store:
            return Response({'error': 'Aucun magasin configuré dans votre entreprise'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate register if provided
        register = None
        reg_val = data.get('register')
        reg_uuid = parse_safe_uuid(reg_val)
        if reg_uuid:
            register = CashRegister.objects.filter(id=reg_uuid, company=company).first()
        elif reg_val:
            register = CashRegister.objects.filter(company=company, code__iexact=str(reg_val).strip()).first()
        if not register and reg_val:
            # Une caisse a ete demandee mais n'existe pas dans cette entreprise :
            # on refuse. Avant, la vente etait silencieusement rattachee a la
            # premiere caisse du catalogue : la cloture et le rapport Z de cette
            # caisse (et ceux de la caisse reellement choisie) devenaient faux.
            return Response({'error': 'Caisse introuvable dans votre entreprise'}, status=status.HTTP_400_BAD_REQUEST)
        if not register:
            # Aucune caisse precise : comportement d'origine (premiere caisse).
            register = CashRegister.objects.filter(company=company).first()

        # Validate customer if provided
        customer = None
        cust_val = data.get('customer')
        cust_uuid = parse_safe_uuid(cust_val)
        if cust_uuid:
            customer = Partner.objects.filter(id=cust_uuid, company=company).first()
        elif cust_val:
            customer = Partner.objects.filter(company=company, name__icontains=str(cust_val).strip()).first()
        if not customer and cust_val:
            # Un client a ete demande mais n'existe pas dans cette entreprise :
            # on refuse. Avant, la vente etait silencieusement imputee au
            # premier client du catalogue : son historique, ses creances et son
            # chiffre d'affaires devenaient faux.
            return Response({'error': 'Client introuvable dans votre entreprise'}, status=status.HTTP_400_BAD_REQUEST)
        if not customer:
            # Aucun client precise (vente comptoir) : comportement d'origine.
            customer = Partner.objects.filter(company=company, partner_type='CUSTOMER').first()

        # Prepare items data with product instances
        items_data = []
        for item_in in data['items']:
            prod_val = item_in.get('product')
            prod_uuid = parse_safe_uuid(prod_val)
            prod = None
            if prod_uuid:
                prod = Product.objects.filter(id=prod_uuid, company=company).first()
            elif prod_val:
                prod = Product.objects.filter(company=company, sku__iexact=str(prod_val).strip()).first() or \
                       Product.objects.filter(company=company, name__icontains=str(prod_val).strip()).first()
            if not prod and prod_val:
                # Un produit a ete demande mais n'existe pas dans cette
                # entreprise : on refuse. Avant, l'application vendait
                # silencieusement le premier produit actif du catalogue : la
                # vente pouvait enregistrer un autre article, ou l'article
                # d'une autre entreprise.
                return Response({'error': f"Produit {prod_val} introuvable dans votre entreprise"}, status=status.HTTP_400_BAD_REQUEST)
            if not prod:
                # Aucun produit precise : comportement d'origine (premier produit actif).
                prod = Product.objects.filter(company=company, is_active=True).first()
            if not prod:
                return Response({'error': f"Produit {prod_val} introuvable"}, status=status.HTTP_400_BAD_REQUEST)

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

        user = request.user if request.user and request.user.is_authenticated else None
        if not user:
            from apps.accounts.models import User
            user = User.objects.filter(company=sale.company).first()

        try:
            payment = SaleService.process_payment(
                company=sale.company,
                sale=sale,
                amount=amount,
                method=method,
                register=sale.register,
                user=user,
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

            # Le remboursement se calcule au prix REELLEMENT paye lors de la
            # vente (celui de la ligne de vente), et non au tarif du jour : si
            # le prix a change depuis la vente, l'ancien code remboursait le
            # nouveau prix, au detriment du commercant ou du client.
            ligne_vente = sale.items.filter(product=prod).first()
            prix_paye = ligne_vente.unit_price if ligne_vente else prod.selling_price

            return_items.append({
                'product': prod,
                'quantity': item_in['quantity'],
                'unit_price': item_in.get('unit_price', prix_paye)
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
