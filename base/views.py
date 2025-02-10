from django.shortcuts import render, get_object_or_404
from .models import Item

def index(request):
    items = Item.objects.all()
    return render(request, "index.html", {"items": items})

def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, "item_detail.html", {"item": item})
