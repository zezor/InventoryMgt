from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'bins', views.BinLocationViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'variants', views.ProductVariantViewSet)
router.register(r'inventory-levels', views.InventoryLevelViewSet)

router.register(r'purchase-orders', views.PurchaseOrderViewSet)
router.register(r'po-lines', views.POLineViewSet)
router.register(r'goods-receipts', views.GoodsReceiptViewSet)
router.register(r'gr-lines', views.GRLineViewSet)

router.register(r'sales-orders', views.SalesOrderViewSet)
router.register(r'so-lines', views.SOLineViewSet)
router.register(r'shipments', views.ShipmentViewSet)
router.register(r'shipment-lines', views.ShipmentLineViewSet)

router.register(r'stock-transfers', views.StockTransferViewSet)
router.register(r'stock-transfer-lines', views.StockTransferLineViewSet)

router.register(r'stock-counts', views.StockCountViewSet)
router.register(r'stock-count-lines', views.StockCountLineViewSet)

router.register(r'inventory-transactions', views.InventoryTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]