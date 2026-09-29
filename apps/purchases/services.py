from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.inventory.services import StockService
from apps.inventory.models import StockMovementType
from apps.sales.models import Payment, PaymentMethod
from .models import (
    Purchase,
    PurchaseItem,
    PurchaseStatus,
    PurchasePaymentStatus,
    PurchaseReturn,
    PurchaseReturnItem
)


class PurchaseService:
    """
    Centralized, transactional domain service for Purchases / Supplier orders.
    Manages supplier order creation, reception (stock increment), payments,
    and returns to suppliers.
    """

    @classmethod
    @transaction.atomic
    def create_purchase(
        cls,
        *,
        company,
        supplier,
        store,
        items_data,
        purchaser=None,
        reference=None,
        notes='',
        auto_receive=False
    ):
        if not items_data:
            raise ValidationError("Une commande d'achat doit comporter au moins un article.")

        if not reference:
            from django.utils import timezone
            import random
            reference = f"ACH-{timezone.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

        purchase = Purchase.objects.create(
            company=company,
            supplier=supplier,
            store=store,
            purchaser=purchaser,
            reference=reference,
            status=PurchaseStatus.DRAFT,
            subtotal_amount=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            total_amount=Decimal('0.00'),
            paid_amount=Decimal('0.00'),
            notes=notes
        )

        subtotal = Decimal('0.00')
        total_tax = Decimal('0.00')

        for item in items_data:
            product = item['product']
            qty = Decimal(str(item['quantity']))
            unit_cost = Decimal(str(item.get('unit_cost', product.cost_price)))
            tax_rate = Decimal(str(item.get('tax_rate', product.tax_rate)))

            line_gross = qty * unit_cost
            line_tax = (line_gross * tax_rate) / Decimal('100.00')
            line_net = line_gross + line_tax

            PurchaseItem.objects.create(
                company=company,
                purchase=purchase,
                product=product,
                quantity=qty,
                unit_cost=unit_cost,
                tax_rate=tax_rate,
                total=line_net
            )

            subtotal += line_gross
            total_tax += line_tax

        purchase.subtotal_amount = subtotal
        purchase.tax_amount = total_tax
        purchase.total_amount = subtotal + total_tax
        purchase.save()

        if auto_receive:
            cls.receive_purchase(purchase, user=purchaser)

        return purchase

    @classmethod
    @transaction.atomic
    def receive_purchase(cls, purchase, user=None):
        """
        Receives goods from supplier:
        - Increments stock levels in the target store.
        - Records StockMovement of type PURCHASE.
        - Updates purchase status to RECEIVED.
        """
        if purchase.status == PurchaseStatus.RECEIVED:
            raise ValidationError("Cet achat a déjà été réceptionné.")
        if purchase.status == PurchaseStatus.CANCELLED:
            raise ValidationError("Impossible de réceptionner un achat annulé.")

        for item in purchase.items.all():
            StockService.record_movement(
                company=purchase.company,
                store=purchase.store,
                product=item.product,
                quantity=item.quantity, # positive
                movement_type=StockMovementType.PURCHASE,
                reference=f"PO-{purchase.reference}",
                reason=f"Réception achat #{purchase.reference}",
                user=user,
                unit_cost=item.unit_cost,
                allow_negative=True
            )

        purchase.status = PurchaseStatus.RECEIVED
        purchase.save()
        return purchase

    @classmethod
    @transaction.atomic
    def process_payment(cls, *, company, purchase, amount, method, user=None, reference=''):
        amount = Decimal(str(amount))
        if amount <= Decimal('0.00'):
            raise ValidationError("Le montant du paiement doit être supérieur à zéro.")

        payment = Payment.objects.create(
            company=company,
            purchase=purchase,
            partner=purchase.supplier,
            amount=amount,
            payment_method=method,
            reference=reference,
            processed_by=user
        )

        purchase.paid_amount += amount
        if purchase.paid_amount >= purchase.total_amount:
            purchase.payment_status = PurchasePaymentStatus.PAID
        elif purchase.paid_amount > Decimal('0.00'):
            purchase.payment_status = PurchasePaymentStatus.PARTIAL

        purchase.save()
        return payment

    @classmethod
    @transaction.atomic
    def cancel_purchase(cls, purchase, user=None, reason=''):
        """
        Cancels a purchase. If already received, decrements stock out.
        """
        if purchase.status == PurchaseStatus.CANCELLED:
            raise ValidationError("Cet achat est déjà annulé.")

        if purchase.status == PurchaseStatus.RECEIVED:
            # Revert stock additions
            for item in purchase.items.all():
                StockService.record_movement(
                    company=purchase.company,
                    store=purchase.store,
                    product=item.product,
                    quantity=-item.quantity, # decrement back
                    movement_type=StockMovementType.RETURN_SUPPLIER,
                    reference=f"CANCEL-PO-{purchase.reference}",
                    reason=f"Annulation commande fournisseur: {reason}",
                    user=user,
                    allow_negative=True
                )

        purchase.status = PurchaseStatus.CANCELLED
        purchase.save()
        return purchase

    @classmethod
    @transaction.atomic
    def process_return(cls, *, purchase, return_items, user=None, reason='', refund_amount=None):
        if purchase.status != PurchaseStatus.RECEIVED:
            raise ValidationError("Un retour fournisseur ne peut être créé que pour un achat réceptionné.")

        from django.utils import timezone
        import random
        ret_ref = f"RET-SUP-{timezone.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

        purchase_return = PurchaseReturn.objects.create(
            company=purchase.company,
            purchase=purchase,
            reference=ret_ref,
            reason=reason,
            processed_by=user,
            refund_amount=Decimal('0.00')
        )

        total_refund = Decimal('0.00')

        for item_data in return_items:
            product = item_data['product']
            qty = Decimal(str(item_data['quantity']))
            unit_cost = Decimal(str(item_data.get('unit_cost', product.cost_price)))

            refund_line = qty * unit_cost
            total_refund += refund_line

            PurchaseReturnItem.objects.create(
                company=purchase.company,
                purchase_return=purchase_return,
                product=product,
                quantity=qty,
                unit_cost=unit_cost,
                refund_total=refund_line
            )

            # Deduct returned stock from store
            StockService.record_movement(
                company=purchase.company,
                store=purchase.store,
                product=product,
                quantity=-qty,
                movement_type=StockMovementType.RETURN_SUPPLIER,
                reference=f"RET-SUP-{purchase.reference}",
                reason=f"Retour fournisseur: {reason}",
                user=user,
                allow_negative=False
            )

        purchase_return.refund_amount = refund_amount if refund_amount is not None else total_refund
        purchase_return.save()
        return purchase_return
