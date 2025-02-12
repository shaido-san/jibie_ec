from django.contrib import admin
from .models import Item, Stock

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
