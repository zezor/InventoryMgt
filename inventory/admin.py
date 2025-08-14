from django.contrib import admin
from .models import (
    Organization, Currency, UnitOfMeasure, UOMConversion,
    Warehouse, BinLocation, Supplier, Customer, Category, Brand,
    Product, ProductVariant, BatchLot, SerialNumber,
    InventoryLevel, InventoryTransaction,
    PurchaseOrder, POLine, GoodsReceipt, GRLine,
    SalesOrder, SOLine, Reservation,
    Shipment, ShipmentLine,
    StockTransfer, StockTransferLine,
    StockCount, StockCountLine,
    PriceList, Price
)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_at")
    search_fields = ("name", "code")

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("organization", "code", "name", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("code", "name")

@admin.register(BinLocation)
class BinAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "code", "is_default", "is_receiving", "is_shipping")
    list_filter = ("warehouse",)
    search_fields = ("code",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("organization", "sku_base", "name", "track_serials", "track_lots", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("sku_base", "name")

@admin.register(ProductVariant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("product", "sku", "barcode")
    search_fields = ("sku", "barcode")

@admin.register(InventoryLevel)
class InventoryLevelAdmin(admin.ModelAdmin):
    list_display = ("variant", "warehouse", "bin", "on_hand", "allocated")
    list_filter = ("warehouse",)
    search_fields = ("variant__sku",)

admin.site.register([
    Currency, UnitOfMeasure, UOMConversion,
    Supplier, Customer, Category, Brand,
    BatchLot, SerialNumber,
    InventoryTransaction,
    PurchaseOrder, POLine, GoodsReceipt, GRLine,
    SalesOrder, SOLine, Reservation,
    Shipment, ShipmentLine,
    StockTransfer, StockTransferLine,
    StockCount, StockCountLine,
    PriceList, Price,
])