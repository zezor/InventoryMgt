from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.paginator import Paginator
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import datetime
from django.db.models import Q
from django.shortcuts import render
from .models import *
from .serializers import *
from .services.inventory import post_goods_receipt_line, post_shipment_line, post_transfer_line, close_and_post_stock_count
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Sale
from .forms import ProductForm, SaleForm
from reportlab.pdfgen import canvas


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

class OrganizationViewSet(BaseViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filterset_fields = ["name", "code"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code", "created_at"]

class WarehouseViewSet(BaseViewSet):
    queryset = Warehouse.objects.select_related("organization").all()
    serializer_class = WarehouseSerializer
    filterset_fields = ["organization", "code", "is_active"]
    search_fields = ["code", "name"]

class BinLocationViewSet(BaseViewSet):
    queryset = BinLocation.objects.select_related("warehouse").all()
    serializer_class = BinLocationSerializer
    filterset_fields = ["warehouse", "code", "is_default", "is_receiving", "is_shipping"]
    search_fields = ["code", "name"]

class ProductViewSet(BaseViewSet):
    queryset = Product.objects.select_related("organization", "category", "brand", "base_uom").all()
    serializer_class = ProductSerializer
    filterset_fields = ["organization", "sku_base", "track_serials", "track_lots", "is_active", "category", "brand"]
    search_fields = ["sku_base", "name"]

class ProductVariantViewSet(BaseViewSet):
    queryset = ProductVariant.objects.select_related("product").all()
    serializer_class = ProductVariantSerializer
    filterset_fields = ["product", "sku", "barcode"]
    search_fields = ["sku", "barcode"]

class InventoryLevelViewSet(BaseViewSet):
    queryset = InventoryLevel.objects.select_related("variant", "warehouse", "bin").all()
    serializer_class = InventoryLevelSerializer
    filterset_fields = ["variant", "warehouse", "bin"]
    ordering_fields = ["on_hand", "allocated", "updated_at"]

# --- Purchasing (Inbound) ---
class PurchaseOrderViewSet(BaseViewSet):
    queryset = PurchaseOrder.objects.select_related("organization", "supplier").all()
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ["organization", "supplier", "status", "code"]
    search_fields = ["code"]

class POLineViewSet(BaseViewSet):
    queryset = POLine.objects.select_related("po", "variant", "uom", "warehouse").all()
    serializer_class = POLineSerializer
    filterset_fields = ["po", "variant", "warehouse"]

class GoodsReceiptViewSet(BaseViewSet):
    queryset = GoodsReceipt.objects.select_related("organization", "supplier", "po").all()
    serializer_class = GoodsReceiptSerializer
    filterset_fields = ["organization", "supplier", "po", "code"]

class GRLineViewSet(BaseViewSet):
    queryset = GRLine.objects.select_related("grn", "variant", "uom", "warehouse", "bin").all()
    serializer_class = GRLineSerializer
    filterset_fields = ["grn", "variant", "warehouse", "bin"]

    @action(detail=True, methods=["post"], url_path="post")
    def post_line(self, request, pk=None):
        line = self.get_object()
        post_goods_receipt_line(line)
        return Response({"status": "posted"})

# --- Sales (Outbound) ---
class SalesOrderViewSet(BaseViewSet):
    queryset = SalesOrder.objects.select_related("organization", "customer").all()
    serializer_class = SalesOrderSerializer
    filterset_fields = ["organization", "customer", "status", "code"]
    search_fields = ["code"]

class SOLineViewSet(BaseViewSet):
    queryset = SOLine.objects.select_related("so", "variant", "uom", "warehouse").all()
    serializer_class = SOLineSerializer
    filterset_fields = ["so", "variant", "warehouse"]

class ShipmentViewSet(BaseViewSet):
    queryset = Shipment.objects.select_related("organization", "sales_order").all()
    serializer_class = ShipmentSerializer
    filterset_fields = ["organization", "sales_order", "code"]

class ShipmentLineViewSet(BaseViewSet):
    queryset = ShipmentLine.objects.select_related("shipment", "variant", "warehouse", "bin").all()
    serializer_class = ShipmentLineSerializer
    filterset_fields = ["shipment", "variant", "warehouse", "bin"]

    @action(detail=True, methods=["post"], url_path="post")
    def post_line(self, request, pk=None):
        line = self.get_object()
        post_shipment_line(line)
        return Response({"status": "posted"})

# --- Internal Movement ---
class StockTransferViewSet(BaseViewSet):
    queryset = StockTransfer.objects.select_related("from_warehouse", "to_warehouse").all()
    serializer_class = StockTransferSerializer
    filterset_fields = ["from_warehouse", "to_warehouse", "code"]

class StockTransferLineViewSet(BaseViewSet):
    queryset = StockTransferLine.objects.select_related("transfer", "variant", "from_bin", "to_bin").all()
    serializer_class = StockTransferLineSerializer
    filterset_fields = ["transfer", "variant", "from_bin", "to_bin"]

    @action(detail=True, methods=["post"], url_path="post")
    def post_line(self, request, pk=None):
        line = self.get_object()
        post_transfer_line(line)
        return Response({"status": "posted"})

# --- Stock Count ---
class StockCountViewSet(BaseViewSet):
    queryset = StockCount.objects.select_related("warehouse").all()
    serializer_class = StockCountSerializer
    filterset_fields = ["warehouse", "status", "code"]

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        count = self.get_object()
        with transaction.atomic():
            count.status = StockCount.Status.CLOSED
            count.save(update_fields=["status"])
            close_and_post_stock_count(count)
        return Response({"status": "closed & posted"})

class StockCountLineViewSet(BaseViewSet):
    queryset = StockCountLine.objects.select_related("count", "variant", "bin").all()
    serializer_class = StockCountLineSerializer
    filterset_fields = ["count", "variant", "bin"]

class InventoryTransactionViewSet(BaseViewSet):
    queryset = InventoryTransaction.objects.select_related("variant", "warehouse_from", "warehouse_to", "bin_from", "bin_to").all()
    serializer_class = InventoryTransactionSerializer
    filterset_fields = ["variant", "type", "warehouse_from", "warehouse_to"]
    ordering_fields = ["occurred_at"]
    
    
    
# inventory/views.py


# def product_list(request):
#     search_query = request.GET.get('q', '')
#     products = Product.objects.all()

#     if search_query:
#         products = products.filter(
#             Q(name__icontains=search_query) | Q(description__icontains=search_query)
#         )

#     paginator = Paginator(products, 10)  # Show 10 products per page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     return render(request, 'product_list.html', {'page_obj': page_obj, 'search_query': search_query})





def sale_receipt_pdf(request, sale_id):
    sale = Sale.objects.get(id=sale_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{sale.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "SALES RECEIPT")
    p.setFont("Helvetica", 12)
    p.drawString(50, 770, f"Date: {datetime.date.today().strftime('%Y-%m-%d')}")
    p.drawString(50, 750, f"Product: {sale.product.name}")
    p.drawString(50, 730, f"Quantity Sold: {sale.quantity_sold}")
    p.drawString(50, 710, f"Unit Price: GHS {sale.product.price}")
    p.drawString(50, 690, f"Total: GHS {sale.total_price}")
    p.showPage()
    p.save()
    return response



# Product List with Search & Pagination
def product_list(request):
    query = request.GET.get('q')
    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/product_list.html', {'page_obj': page_obj, 'query': query})

# Add Product
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/add_product.html', {'form': form})

# Record Sale + Generate PDF Receipt
def record_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            return redirect('generate_receipt', sale_id=sale.id)
    else:
        form = SaleForm()
    return render(request, 'inventory/record_sale.html', {'form': form})

# Generate PDF Receipt
def generate_receipt(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{sale.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Sales Receipt")

    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Receipt ID: {sale.id}")
    p.drawString(50, height - 120, f"Date: {sale.date}")
    p.drawString(50, height - 140, f"Product: {sale.product.name}")
    p.drawString(50, height - 160, f"Quantity: {sale.quantity}")
    p.drawString(50, height - 180, f"Unit Price: {sale.product.price}")
    p.drawString(50, height - 200, f"Total: {sale.total_price}")

    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, height - 240, "Thank you for your purchase!")

    p.showPage()
    p.save()

    return response


def dashboard(request):
    return render(request, 'dashboard.html')


def sales_report(request):
    return render(request, 'sales_report.html')

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')  # Redirect to login page after logout

def login_view(request):
    from django.contrib.auth import authenticate, login
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard after login
        else:
            return render(request, 'auth/login.html', {'error': 'Invalid credentials'})
    return render(request, 'auth/login.html')