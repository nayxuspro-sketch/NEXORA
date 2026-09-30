from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.inventory.services import StockService
from apps.inventory.models import StockMovementType
from apps.pos.models import CashRegister, RegisterStatus
from .models import (
    Sale,
    SaleItem,
    SaleStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
    SaleReturn,
    SaleReturnItem
)


class SaleService:
    """
    Centralized, transactional business logic for Sales, Payments, and Returns.
    Ensures complete atomicity: stock checks, line creations, movement logs,
    register update and balance adjustments.
    """

    @classmethod
    @transaction.atomic
    def create_and_complete_sale(
        cls,
        *,
        company,
        store,
        items_data,
        seller=None,
        customer=None,
        register=None,
        reference=None,
        payment_data=None,
        discount_amount=Decimal('0.00'),
        notes=''
    ):
        """
        Executes full sale lifecycle transactionally:
        1. Checks stock availability for all items.
        2. Creates Sale header.
        3. Creates SaleItem lines with tax calculations.
        4. Decrements inventory stock & registers StockMovement records.
        5. Handles immediate payment (if provided) & updates register balance.
        6. In case of error (e.g. stock shortfall), entire transaction rolls back.
        """
        if not items_data:
            raise ValidationError("Une vente doit comporter au moins un article.")

        # 1. Pre-validation and stock availability check
        for item in items_data:
            product = item['product']
            qty = Decimal(str(item['quantity']))
            if qty <= Decimal('0.00'):
                raise ValidationError(f"La quantité pour '{product.name}' doit être positive.")

            # Check stock in store
            stock_level = store.stock_levels.filter(product=product).first()
            available = stock_level.quantity if stock_level else Decimal('0.00')
            if available < qty:
                raise ValidationError(
                    f"Stock insuffisant pour le produit '{product.name}'. "
                    f"Disponible: {available}, Demandé: {qty}."
                )

        # Generate reference if omitted
        if not reference:
            from django.utils import timezone
            import random
            reference = f"VNT-{timezone.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

        # 2. Create Sale Header
        sale = Sale.objects.create(
            company=company,
            store=store,
            register=register,
            customer=customer,
            seller=seller,
            reference=reference,
            status=SaleStatus.COMPLETED,
            subtotal_amount=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            total_amount=Decimal('0.00'),
            paid_amount=Decimal('0.00'),
            discount_amount=Decimal(str(discount_amount)),
            notes=notes
        )

        subtotal = Decimal('0.00')
        total_tax = Decimal('0.00')

        # 3. Create lines & 4. Deduct stock
        for item in items_data:
            product = item['product']
            qty = Decimal(str(item['quantity']))
            unit_price = Decimal(str(item.get('unit_price', product.selling_price)))
            tax_rate = Decimal(str(item.get('tax_rate', product.tax_rate)))
            line_discount = Decimal(str(item.get('discount_rate', '0.00')))

            line_gross = qty * unit_price
            line_disc_val = (line_gross * line_discount) / Decimal('100.00')
            line_tax_val = ((line_gross - line_disc_val) * tax_rate) / Decimal('100.00')
            line_net = (line_gross - line_disc_val) + line_tax_val

            SaleItem.objects.create(
                company=company,
                sale=sale,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                tax_rate=tax_rate,
                discount_rate=line_discount,
                total=line_net
            )

            subtotal += (line_gross - line_disc_val)
            total_tax += line_tax_val

            # Transactional stock deduction
            StockService.record_movement(
                company=company,
                store=store,
                product=product,
                quantity=-qty,
                movement_type=StockMovementType.SALE,
                reference=f"SALE-{sale.reference}",
                reason=f"Vente #{sale.reference}",
                user=seller,
                unit_cost=product.cost_price,
                allow_negative=False
            )

        sale.subtotal_amount = subtotal
        sale.tax_amount = total_tax
        sale.total_amount = max(Decimal('0.00'), (subtotal + total_tax) - sale.discount_amount)

        # 5. Process Payment if provided
        if payment_data:
            cls.process_payment(
                company=company,
                sale=sale,
                amount=payment_data.get('amount', sale.total_amount),
                method=payment_data.get('method', PaymentMethod.CASH),
                register=register,
                user=seller,
                reference=payment_data.get('reference', '')
            )
        else:
            sale.payment_status = PaymentStatus.PENDING

        sale.save()
        return sale

    @classmethod
    @transaction.atomic
    def process_payment(cls, *, company, sale, amount, method, register=None, user=None, reference=''):
        """
        Records a payment towards a sale.
        Updates sale paid_amount and payment_status.
        If CASH and register is specified, increments cash register current_balance.
        """
        amount = Decimal(str(amount))
        if amount <= Decimal('0.00'):
            raise ValidationError("Le montant du paiement doit être supérieur à zéro.")

        payment = Payment.objects.create(
            company=company,
            sale=sale,
            amount=amount,
            payment_method=method,
            register=register,
            reference=reference,
            processed_by=user
        )

        sale.paid_amount += amount
        if sale.paid_amount >= sale.total_amount:
            sale.payment_status = PaymentStatus.PAID
        elif sale.paid_amount > Decimal('0.00'):
            sale.payment_status = PaymentStatus.PARTIAL

        sale.save()

        # Update cash register balance if cash payment
        if register and method == PaymentMethod.CASH:
            register.current_balance += amount
            register.save()

        # Update customer balance if applicable
        if sale.customer and method == PaymentMethod.CREDIT:
            sale.customer.current_balance += amount
            sale.customer.save()

        return payment

    @classmethod
    @transaction.atomic
    def cancel_sale(cls, sale, user=None, reason=''):
        """
        Cancels a sale, reverts all stock deductions, and adjusts payments.
        """
        if sale.status == SaleStatus.CANCELLED:
            raise ValidationError("Cette vente est déjà annulée.")

        for item in sale.items.all():
            StockService.record_movement(
                company=sale.company,
                store=sale.store,
                product=item.product,
                quantity=item.quantity, # positive adjustment to restore
                movement_type=StockMovementType.RETURN_CUSTOMER,
                reference=f"CANCEL-{sale.reference}",
                reason=f"Annulation vente: {reason}",
                user=user,
                allow_negative=True
            )

        sale.status = SaleStatus.CANCELLED
        sale.save()
        return sale

    @classmethod
    @transaction.atomic
    def process_return(cls, *, sale, return_items, user=None, reason='', refund_amount=None):
        """
        Processes a partial or full customer return:
        - Restores returned items back into store inventory.
        - Records SaleReturn and SaleReturnItem records.
        """
        if sale.status == SaleStatus.CANCELLED:
            raise ValidationError("Impossible d'effectuer un retour sur une vente déjà annulée.")

        from django.utils import timezone
        import random
        ret_ref = f"RET-{timezone.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

        total_refund = Decimal('0.00')

        sale_return = SaleReturn.objects.create(
            company=sale.company,
            sale=sale,
            reference=ret_ref,
            reason=reason,
            processed_by=user,
            refund_amount=Decimal('0.00')
        )

        for item_data in return_items:
            product = item_data['product']
            qty = Decimal(str(item_data['quantity']))
            unit_price = Decimal(str(item_data.get('unit_price', product.selling_price)))

            # Check that item was part of sale
            sale_item = sale.items.filter(product=product).first()
            if not sale_item:
                raise ValidationError(f"Le produit {product.name} n'appartient pas à cette vente.")
            if qty > sale_item.quantity:
                raise ValidationError(f"Quantité de retour ({qty}) supérieure à la quantité vendue ({sale_item.quantity}).")

            refund_line = qty * unit_price
            total_refund += refund_line

            SaleReturnItem.objects.create(
                company=sale.company,
                sale_return=sale_return,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                refund_total=refund_line
            )

            # Replenish stock
            StockService.record_movement(
                company=sale.company,
                store=sale.store,
                product=product,
                quantity=qty,
                movement_type=StockMovementType.RETURN_CUSTOMER,
                reference=f"RET-{sale.reference}",
                reason=f"Retour client: {reason}",
                user=user,
                allow_negative=True
            )

        sale_return.refund_amount = refund_amount if refund_amount is not None else total_refund
        sale_return.save()
        return sale_return
