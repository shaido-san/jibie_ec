from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from .models import Item, Cart
from django.db import transaction

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 登録後に自動ログインするコード
            login(request, user)
            return redirect("index")
        
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})
    
class CustomLoginView(LoginView):
    template_name = "login.html"

class CustomLogoutView(LogoutView):
    next_page = "login"

@login_required
def index(request):
    items = Item.objects.all()
    return render(request, "index.html", {"items": items})

def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    stock_item_range = range(1, item.get_stock() + 1)
    return render(request, "item_detail.html", {"item": item, "stock_item_range":stock_item_range})

def cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)

    total_price = 0
    cart_data = []

    for cart_item in cart_items:
        image_url = cart_item.item.image.url if cart_item.item.image else None
        subtotal = cart_item.item.price * cart_item.quantity
        cart_data.append({
            "item":cart_item.item,
            "image_url": image_url,
            "quantity": cart_item.quantity,
            "subtotal": subtotal
        })
        total_price += subtotal
    return render(request, "cart.html", {"cart": cart_data, "total_price":total_price})
    
def add_to_cart(request, item_id):

# 辞書型の中の辞書の構造になっている。例が下になる。また、ここではカートに商品を入れた時に、まだStockテーブルの更新は行わない。
#     cart = {
#     "1": {
#         "name": "鹿肉セット",
#         "price": 5000,
#         "quantity": 2
#     },
#     "2": {
#         "name": "猪肉ステーキ",
#         "price": 3000,
#         "quantity": 1
#     }
# }
    item = get_object_or_404(Item, id=item_id)
    user = request.user

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        
        # ここのget_stockはItemモデルに紐づいているStockテーブルのquantityを呼び出している。models.pyにメソッドがある。
        available_stock = item.get_stock()

        if quantity > available_stock:
            print("申し訳ありません。在庫不足です。")
            return redirect("item_detail", item_id=item.id)
        
        cart_item, created = Cart.objects.get_or_create(user=user, item=item, defaults={"quantity": 0})

        if cart_item.quantity + quantity <= available_stock:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            print("カート内の数量が在庫を超過しているため、追加できません。")
    
    return redirect("cart")
    

    
