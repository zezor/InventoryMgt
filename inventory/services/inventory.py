# Create directory inventory/services/__init__.py (empty) and inventory/services/inventory.py with:
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from ..models import InventoryLevel, InventoryTransaction, GRLine, ShipmentLine, StockTransferLine, StockCount, StockCountLine


def _get_or_create_level(variant, warehouse, bin):
    level, _ = InventoryLevel.objects.get_or_create(
        variant=variant, warehouse=warehouse, bin=bin,
        defaults={"on_hand": Decimal("0"), "allocated": Decimal("0")}
    )
    return level


@transaction.atomic
def post_goods_receipt_line(gr_line: GRLine):
    variant = gr_line.variant
    warehouse = gr_line.warehouse
    bin = gr_line.bin
    qty = gr_line.qty_received
    uom = gr_line.uom

    # Update on_hand
    level = _get_or_create_level(variant, warehouse, bin)
    # Lock row to prevent races
    level = InventoryLevel.objects.select_for_update().get(pk=level.pk)
    level.on_hand = F('on_hand') + qty
    level.save(update_fields=["on_hand"])

    # Ledger
    InventoryTransaction.objects.create(
        organization=warehouse.organization,
        variant=variant,
        uom=uom,
        qty=qty,
        type=InventoryTransaction.Types.RECEIVE,
        warehouse_to=warehouse,
        bin_to=bin,
        batch=gr_line.batch,
        source_type="GRLine",
        source_id=str(gr_line.id),
        note=f"GRN {gr_line.grn.code}"
    )


@transaction.atomic
def post_shipment_line(line: ShipmentLine):
    variant = line.variant
    warehouse = line.warehouse
    bin = line.bin
    qty = line.qty
    uom = variant.product.base_uom  # or line-specific uom if present

    level = _get_or_create_level(variant, warehouse, bin)
    level = InventoryLevel.objects.select_for_update().get(pk=level.pk)

    # Ensure sufficient stock
    level.refresh_from_db()
    if level.on_hand < qty:
        raise ValidationError("Insufficient on-hand to ship")

    level.on_hand = F('on_hand') - qty
    # Optionally reduce allocated if this was reserved
    if level.allocated > 0:
        level.allocated = F('allocated') - min(level.allocated, qty)
    level.save(update_fields=["on_hand", "allocated"])

    InventoryTransaction.objects.create(
        organization=warehouse.organization,
        variant=variant,
        uom=uom,
        qty=qty,
        type=InventoryTransaction.Types.SHIP,
        warehouse_from=warehouse,
        bin_from=bin,
        serial=line.serial,
        batch=line.batch,
        source_type="ShipmentLine",
        source_id=str(line.id),
        note=f"Shipment {line.shipment.code}"
    )


@transaction.atomic
def post_transfer_line(tline: StockTransferLine):
    variant = tline.variant
    from_bin = tline.from_bin
    to_bin = tline.to_bin
    qty = tline.qty
    uom = variant.product.base_uom

    # Decrease from
    from_level = _get_or_create_level(variant, from_bin.warehouse, from_bin)
    from_level = InventoryLevel.objects.select_for_update().get(pk=from_level.pk)
    if from_level.on_hand < qty:
        raise ValidationError("Insufficient stock in source bin")
    from_level.on_hand = F('on_hand') - qty
    from_level.save(update_fields=["on_hand"])

    InventoryTransaction.objects.create(
        organization=from_bin.warehouse.organization,
        variant=variant,
        uom=uom,
        qty=qty,
        type=InventoryTransaction.Types.TRANSFER,
        warehouse_from=from_bin.warehouse,
        bin_from=from_bin,
        warehouse_to=to_bin.warehouse,
        bin_to=to_bin,
        source_type="StockTransferLine",
        source_id=str(tline.id),
        note=f"Transfer {tline.transfer.code}"
    )

    # Increase to
    to_level = _get_or_create_level(variant, to_bin.warehouse, to_bin)
    to_level = InventoryLevel.objects.select_for_update().get(pk=to_level.pk)
    to_level.on_hand = F('on_hand') + qty
    to_level.save(update_fields=["on_hand"])


@transaction.atomic
def close_and_post_stock_count(count: StockCount):
    # For each line, set on_hand to counted and log COUNT adjustment
    for line in StockCountLine.objects.select_for_update().filter(count=count):
        level = _get_or_create_level(line.variant, count.warehouse, line.bin)
        level = InventoryLevel.objects.select_for_update().get(pk=level.pk)
        delta = line.counted_qty - level.on_hand
        if delta != 0:
            level.on_hand = F('on_hand') + delta
            level.save(update_fields=["on_hand"])
            InventoryTransaction.objects.create(
                organization=count.warehouse.organization,
                variant=line.variant,
                uom=line.variant.product.base_uom,
                qty=delta,
                type=InventoryTransaction.Types.COUNT,
                warehouse_from=count.warehouse if delta < 0 else None,
                bin_from=line.bin if delta < 0 else None,
                warehouse_to=count.warehouse if delta > 0 else None,
                bin_to=line.bin if delta > 0 else None,
                source_type="StockCount",
                source_id=str(count.id),
                note=f"Stock count {count.code}"
            )