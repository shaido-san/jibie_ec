from django.contrib import admin
from .models import Item, Stock, Order, OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "address", "total_price", "created_at")  # 一覧表示
    list_filter = ("created_at",)  # 作成日でフィルタリング
    search_fields = ("user__username", "address__name")  # 検索フィールド

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "item", "quantity", "subtotal_price")  # 一覧表示
    list_filter = ("order",)  # 注文ごとにフィルタリング
    search_fields = ("item__name",)  # 商品名で検索
class StockInLine(admin.StackedInline):
    model = Stock
    extra = 1
class ItemAdmin(admin.ModelAdmin):
    list_display = ["name", "get_stock", "created_at"]
    inlines = [StockInLine]

    def get_stock(self, obj):
        stock = Stock.objects.filter(item=obj).first()
        return stock.quantity if stock else 0
    get_stock.short_description = "在庫"
    
admin.site.register(Item, ItemAdmin)
