from rest_framework import serializers
from .models import *

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = "__all__"

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"

class BinLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BinLocation
        fields = "__all__"

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = "__all__"

class InventoryLevelSerializer(serializers.ModelSerializer):
    available = serializers.DecimalField(max_digits=16, decimal_places=3, read_only=True)

    class Meta:
        model = InventoryLevel
        fields = [
            'id','variant','warehouse','bin','on_hand','allocated','safety_stock','reorder_point','available',
            'created_at','updated_at'
        ]

class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"

class POLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = POLine
        fields = "__all__"

class GoodsReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceipt
        fields = "__all__"

class GRLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = GRLine
        fields = "__all__"

class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = "__all__"

class SOLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOLine
        fields = "__all__"

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = "__all__"

class ShipmentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentLine
        fields = "__all__"

class StockTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransfer
        fields = "__all__"

class StockTransferLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransferLine
        fields = "__all__"

class StockCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCount
        fields = "__all__"

class StockCountLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCountLine
        fields = "__all__"

class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = "__all__"