"""
Advanced Inventory Management System — ERD (ASCII) + Django Models
------------------------------------------------------------------

LEGEND: (1)---< (many), [PK]=primary key, [FK]=foreign key

[Organization]
    └──(1)---<[Warehouse]
                 └──(1)---<[BinLocation]

[Organization]
    ├──(1)---<[Supplier]
    ├──(1)---<[Customer]
    ├──(1)---<[Category] (self-parented tree)
    ├──(1)---<[UnitOfMeasure]
    │               └──(1)---<[UOMConversion] (from_uom,to_uom,F:I factor)
    └──(1)---<[Product]
                     └──(1)---<[ProductVariant]
                                   ├──(1)---<[BatchLot]
                                   └──(1)---<[SerialNumber]

[ProductVariant]---<(many) [InventoryLevel] >---(1)[Warehouse]
                                        └---(1)[BinLocation]

Commercial Flow (Buy):
[PurchaseOrder]---<(many)[POLine] -> (upon receipt)
[GoodsReceipt]---<(many)[GRLine] -> creates [InventoryTransaction] + updates [InventoryLevel]

Commercial Flow (Sell):
[SalesOrder]---<(many)[SOLine] -> (reserve/pick/ship)
[Reservation] -> [Shipment]---<(many)[ShipmentLine] -> [InventoryTransaction]

Internal Movement/Control:
[StockTransfer]---<(many)[StockTransferLine] -> [InventoryTransaction]
[StockCount]---<(many)[StockCountLine] -> [InventoryTransaction]

Auditing:
- All models inherit TimeStampedModel (created/updated + user)
- InventoryTransaction keeps the authoritative movement ledger

"""
from uuid import uuid4
from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal


# ----------------------------
# Mixins / Base Models
# ----------------------------
class TimeStampedModel(models.Model):
    """Common audit fields for all tables."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="%(class)s_created",
        on_delete=models.SET_NULL
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="%(class)s_updated",
        on_delete=models.SET_NULL
    )

    class Meta:
        abstract = True


# ----------------------------
# Master Data
# ----------------------------
class Organization(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Currency(TimeStampedModel):
    code = models.CharField(max_length=3, unique=True)  # e.g., USD, GHS
    symbol = models.CharField(max_length=5, blank=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.code


class UnitOfMeasure(TimeStampedModel):
    EACH = "EA"
    WEIGHT = "WT"
    VOLUME = "VOL"
    LENGTH = "LEN"
    AREA = "AREA"
    TYPES = [
        (EACH, "Each"),
        (WEIGHT, "Weight"),
        (VOLUME, "Volume"),
        (LENGTH, "Length"),
        (AREA, "Area"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="uoms")
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)
    kind = models.CharField(max_length=5, choices=TYPES, default=EACH)
    is_base = models.BooleanField(default=False, help_text="Base UoM for its kind inside this org")

    class Meta:
        unique_together = ("organization", "abbreviation")

    def __str__(self):
        return f"{self.abbreviation} ({self.organization.code})"


class UOMConversion(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="uom_conversions")
    from_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name="conversions_from")
    to_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name="conversions_to")
    factor = models.DecimalField(max_digits=16, decimal_places=6, help_text="Multiply by this to convert from->to")

    class Meta:
        unique_together = ("organization", "from_uom", "to_uom")

    def __str__(self):
        return f"1 {self.from_uom.abbreviation} = {self.factor} {self.to_uom.abbreviation}"


class Warehouse(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="warehouses")
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "code")
        indexes = [models.Index(fields=["organization", "code"]) ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class BinLocation(TimeStampedModel):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="bins")
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    is_receiving = models.BooleanField(default=False)
    is_shipping = models.BooleanField(default=False)

    class Meta:
        unique_together = ("warehouse", "code")
        indexes = [models.Index(fields=["warehouse", "code"]) ]

    def __str__(self):
        return f"{self.warehouse.code}:{self.code}"


class Supplier(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="suppliers")
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class Customer(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="customers")
    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class Category(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=120)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")

    class Meta:
        unique_together = ("organization", "name")
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Brand(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="brands")
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    sku_base = models.SlugField(max_length=60, help_text="Base/parent SKU")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    base_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="products")
    track_serials = models.BooleanField(default=False)
    track_lots = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "sku_base")
        indexes = [models.Index(fields=["organization", "sku_base"]) ]

    def __str__(self):
        return f"{self.sku_base} - {self.name}"


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.SlugField(max_length=80)
    attributes = models.JSONField(default=dict, blank=True, help_text="e.g., {color: 'Red', size: 'M'}")
    barcode = models.CharField(max_length=80, blank=True)
    sell_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="variants_as_sell_uom")
    purchase_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="variants_as_purchase_uom")

    class Meta:
        unique_together = ("product", "sku")
        indexes = [models.Index(fields=["sku"]) ]

    def __str__(self):
        return self.sku


class BatchLot(TimeStampedModel):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="batches")
    code = models.CharField(max_length=80)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("variant", "code")

    def __str__(self):
        return f"{self.variant.sku}:{self.code}"


class SerialNumber(TimeStampedModel):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="serials")
    serial = models.CharField(max_length=120)
    batch = models.ForeignKey(BatchLot, null=True, blank=True, on_delete=models.SET_NULL, related_name="serials")

    class Meta:
        unique_together = ("variant", "serial")

    def __str__(self):
        return self.serial


# ----------------------------
# Inventory
# ----------------------------
class InventoryLevel(TimeStampedModel):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="inventory_levels")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventory_levels")
    bin = models.ForeignKey(BinLocation, on_delete=models.CASCADE, related_name="inventory_levels")
    on_hand = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    allocated = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    safety_stock = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    reorder_point = models.DecimalField(max_digits=16, decimal_places=3, default=0)

    class Meta:
        unique_together = ("variant", "bin")
        indexes = [
            models.Index(fields=["variant", "warehouse"]),
            models.Index(fields=["warehouse", "bin"]),
        ]

    @property
    def available(self):
        return self.on_hand - self.allocated

    def __str__(self):
        return f"{self.variant.sku}@{self.bin} = {self.on_hand}"


class InventoryTransaction(TimeStampedModel):
    class Types(models.TextChoices):
        RECEIVE = "RECEIVE", "Receive"
        ISSUE = "ISSUE", "Issue/Consume"
        ADJUST = "ADJUST", "Adjustment"
        TRANSFER = "TRANSFER", "Transfer"
        RESERVE = "RESERVE", "Reserve"
        RELEASE = "RELEASE", "Release Reservation"
        PICK = "PICK", "Pick"
        PACK = "PACK", "Pack"
        SHIP = "SHIP", "Ship"
        RETURN_PO = "RETURN_PO", "Return to Supplier"
        RETURN_SO = "RETURN_SO", "Return from Customer"
        COUNT = "COUNT", "Stock Count Adjustment"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="inventory_transactions")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="transactions")
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)

    qty = models.DecimalField(max_digits=16, decimal_places=3)
    type = models.CharField(max_length=20, choices=Types.choices)

    warehouse_from = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.PROTECT, related_name="transfers_out")
    bin_from = models.ForeignKey(BinLocation, null=True, blank=True, on_delete=models.PROTECT, related_name="transfers_out")
    warehouse_to = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.PROTECT, related_name="transfers_in")
    bin_to = models.ForeignKey(BinLocation, null=True, blank=True, on_delete=models.PROTECT, related_name="transfers_in")

    batch = models.ForeignKey(BatchLot, null=True, blank=True, on_delete=models.SET_NULL)
    serial = models.ForeignKey(SerialNumber, null=True, blank=True, on_delete=models.SET_NULL)

    # Optional linkage to source docs (keep it simple + portable across DBs)
    source_type = models.CharField(max_length=40, blank=True)
    source_id = models.CharField(max_length=40, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "occurred_at"]),
            models.Index(fields=["variant", "occurred_at"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):
        return f"{self.type} {self.qty} {self.uom.abbreviation} {self.variant.sku}"


# ----------------------------
# Purchasing (Inbound)
# ----------------------------
class PurchaseOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open"
        PARTIAL = "PARTIAL", "Partially Received"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="purchase_orders")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    code = models.CharField(max_length=30)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    ordered_at = models.DateTimeField(null=True, blank=True)
    expected_at = models.DateTimeField(null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("organization", "code")
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO {self.code}"


class POLine(TimeStampedModel):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True)
    qty_ordered = models.DecimalField(max_digits=16, decimal_places=3)
    qty_received = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    requested_bin = models.ForeignKey(BinLocation, null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.po.code}:{self.variant.sku}"


class GoodsReceipt(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="goods_receipts")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    po = models.ForeignKey(PurchaseOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name="receipts")
    code = models.CharField(max_length=30)
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return f"GRN {self.code}"


class GRLine(TimeStampedModel):
    grn = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    po_line = models.ForeignKey(POLine, null=True, blank=True, on_delete=models.SET_NULL, related_name="gr_lines")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    qty_received = models.DecimalField(max_digits=16, decimal_places=3)
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    bin = models.ForeignKey(BinLocation, on_delete=models.PROTECT)
    batch = models.ForeignKey(BatchLot, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.grn.code}:{self.variant.sku} x {self.qty_received}"


# ----------------------------
# Sales (Outbound)
# ----------------------------
class SalesOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open"
        ALLOCATED = "ALLOCATED", "Allocated"
        PARTIAL = "PARTIAL", "Partially Shipped"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sales_orders")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    code = models.CharField(max_length=30)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    ordered_at = models.DateTimeField(null=True, blank=True)
    promised_at = models.DateTimeField(null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("organization", "code")
        ordering = ["-created_at"]

    def __str__(self):
        return f"SO {self.code}"


class SOLine(TimeStampedModel):
    so = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True)
    qty_ordered = models.DecimalField(max_digits=16, decimal_places=3)
    qty_shipped = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.so.code}:{self.variant.sku}"


class Reservation(TimeStampedModel):
    so_line = models.ForeignKey(SOLine, on_delete=models.CASCADE, related_name="reservations")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    bin = models.ForeignKey(BinLocation, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=16, decimal_places=3)

    def __str__(self):
        return f"RES {self.so_line.so.code}:{self.variant.sku} {self.qty}"


class Shipment(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="shipments")
    sales_order = models.ForeignKey(SalesOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name="shipments")
    code = models.CharField(max_length=30)
    shipped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return f"SHP {self.code}"


class ShipmentLine(TimeStampedModel):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="lines")
    so_line = models.ForeignKey(SOLine, null=True, blank=True, on_delete=models.SET_NULL, related_name="shipment_lines")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=16, decimal_places=3)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    bin = models.ForeignKey(BinLocation, on_delete=models.PROTECT)
    serial = models.ForeignKey(SerialNumber, null=True, blank=True, on_delete=models.SET_NULL)
    batch = models.ForeignKey(BatchLot, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.shipment.code}:{self.variant.sku} x {self.qty}"


# ----------------------------
# Internal Movements & Control
# ----------------------------
class StockTransfer(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="stock_transfers")
    code = models.CharField(max_length=30)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="outgoing_transfers")
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="incoming_transfers")
    transferred_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return f"ST {self.code}"


class StockTransferLine(TimeStampedModel):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=16, decimal_places=3)
    from_bin = models.ForeignKey(BinLocation, on_delete=models.PROTECT, related_name="transfer_lines_from")
    to_bin = models.ForeignKey(BinLocation, on_delete=models.PROTECT, related_name="transfer_lines_to")

    def __str__(self):
        return f"{self.transfer.code}:{self.variant.sku} {self.qty}"


class StockCount(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        CLOSED = "CLOSED", "Closed"

    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stock_counts")
    code = models.CharField(max_length=30)
    scheduled_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)

    class Meta:
        unique_together = ("warehouse", "code")

    def __str__(self):
        return f"COUNT {self.code}"


class StockCountLine(TimeStampedModel):
    count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    bin = models.ForeignKey(BinLocation, on_delete=models.PROTECT)
    system_qty = models.DecimalField(max_digits=16, decimal_places=3)
    counted_qty = models.DecimalField(max_digits=16, decimal_places=3)
    variance_note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.count.code}:{self.variant.sku}@{self.bin}"


# ----------------------------
# OPTIONAL: Pricing (simple)
# ----------------------------
class PriceList(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="price_lists")
    name = models.CharField(max_length=100)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class Price(TimeStampedModel):
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name="prices")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="prices")
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4)
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("price_list", "variant", "uom", "valid_from")
        indexes = [models.Index(fields=["variant", "valid_from"]) ]

    def __str__(self):
        return f"{self.variant.sku} @ {self.unit_price}"
    
    
class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    date_sold = models.DateTimeField(default=timezone.now)
    sold_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sales'
    )
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_contact = models.CharField(max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically calculate total price before saving
        if not self.price_at_sale:
            self.price_at_sale = self.product.price
        self.total_price = Decimal(self.quantity) * self.price_at_sale

        # Reduce stock from product
        if self.pk is None:  # Only deduct stock on first save
            self.product.stock_quantity -= self.quantity
            self.product.save()

        super(Sale, self).save(*args, **kwargs)

    def __str__(self):
        return f"Sale of {self.quantity} x {self.product.name} on {self.date_sold.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-date_sold']