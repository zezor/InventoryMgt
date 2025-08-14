from django.test import TestCase
from django.contrib.auth import get_user_model
from inventory.models import *
from inventory.services.inventory import post_goods_receipt_line

class InventorySmokeTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("u@example.com", password="pass")
        self.org = Organization.objects.create(name="Acme", code="acme")
        self.uom = UnitOfMeasure.objects.create(organization=self.org, name="Each", abbreviation="EA", is_base=True)
        self.wh = Warehouse.objects.create(organization=self.org, code="wh1", name="Main")
        self.bin = BinLocation.objects.create(warehouse=self.wh, code="A1")
        self.prod = Product.objects.create(organization=self.org, name="Widget", sku_base="WIDG", base_uom=self.uom)
        self.var = ProductVariant.objects.create(product=self.prod, sku="WIDG-STD", sell_uom=self.uom, purchase_uom=self.uom)

    def test_receipt_posts_inventory(self):
        gr = GoodsReceipt.objects.create(organization=self.org, supplier=Supplier.objects.create(organization=self.org, code="sup", name="Supplier"), code="GR1")
        line = GRLine.objects.create(grn=gr, variant=self.var, qty_received=5, uom=self.uom, warehouse=self.wh, bin=self.bin)
        post_goods_receipt_line(line)
        level = InventoryLevel.objects.get(variant=self.var, bin=self.bin)
        self.assertEqual(level.on_hand, 5)
