from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Store, StockLevel, StockMovement, StockMovementType, Inventory, InventoryLine, InventoryStatus


class StockService:
    """
    Centralized, transactional domain service for all inventory operations.
    Guarantees ACID transactions, avoids race conditions via select_for_update,
    and maintains historical traceability with StockMovement records.
    """

    @classmethod
    @transaction.atomic
    def record_movement(
        cls,
        *,
        company,
        store,
        product,
        quantity,
        movement_type,
        reference='',
        reason='',
        user=None,
        unit_cost=None,
        allow_negative=False
    ):
        """
        Records a movement of inventory.
        quantity: Decimal or float. Positive for adding stock, negative for removing.
        """
        quantity = Decimal(str(quantity))
        if quantity == Decimal('0.00'):
            return None

        # Lock the StockLevel record to avoid race conditions
        stock_level, created = StockLevel.objects.select_for_update().get_or_create(
            company=company,
            store=store,
            product=product,
            defaults={'quantity': Decimal('0.00')}
        )

        current_qty = stock_level.quantity
        new_qty = current_qty + quantity

        if not allow_negative and new_qty < Decimal('0.00'):
            raise ValidationError(
                f"Stock insuffisant pour '{product.name}' dans le magasin '{store.name}'. "
                f"Disponible: {current_qty}, Demandé: {abs(quantity)}."
            )

        stock_level.quantity = new_qty
        stock_level.save()

        # Determine unit cost
        cost = unit_cost if unit_cost is not None else product.cost_price

        movement = StockMovement.objects.create(
            company=company,
            store=store,
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            quantity_before=current_qty,
            quantity_after=new_qty,
            unit_cost=cost,
            reference=reference,
            reason=reason,
            user=user
        )

        return movement

    @classmethod
    @transaction.atomic
    def transfer_stock(cls, *, company, source_store, target_store, product, quantity, user=None, reason=''):
        """
        Transfer stock between two stores transactionally.
        """
        quantity = abs(Decimal(str(quantity)))
        if source_store.id == target_store.id:
            raise ValidationError("Le magasin source et le magasin destination doivent être différents.")

        # Outflow from source
        out_move = cls.record_movement(
            company=company,
            store=source_store,
            product=product,
            quantity=-quantity,
            movement_type=StockMovementType.TRANSFER_OUT,
            reference=f"TRF->{target_store.code}",
            reason=reason,
            user=user
        )

        # Inflow into target
        in_move = cls.record_movement(
            company=company,
            store=target_store,
            product=product,
            quantity=quantity,
            movement_type=StockMovementType.TRANSFER_IN,
            reference=f"TRF<-{source_store.code}",
            reason=reason,
            user=user
        )

        return out_move, in_move

    @classmethod
    @transaction.atomic
    def validate_inventory(cls, inventory, user=None):
        """
        Validates inventory count lines and automatically applies stock adjustments.
        """
        if inventory.status == InventoryStatus.VALIDATED:
            raise ValidationError("Cet inventaire est déjà validé.")

        for line in inventory.lines.select_related('product'):
            diff = line.counted_quantity - line.expected_quantity
            line.difference = diff
            line.save()

            if diff != Decimal('0.00'):
                movement_type = StockMovementType.ADJUSTMENT_IN if diff > 0 else StockMovementType.ADJUSTMENT_OUT
                cls.record_movement(
                    company=inventory.company,
                    store=inventory.store,
                    product=line.product,
                    quantity=diff,
                    movement_type=movement_type,
                    reference=f"INV-{inventory.reference}",
                    reason=f"Ajustement d'inventaire: {line.notes or 'Régularisation'}",
                    user=user,
                    allow_negative=True
                )

        inventory.status = InventoryStatus.VALIDATED
        inventory.validated_at = timezone.now()
        inventory.save()
        return inventory
