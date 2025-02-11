from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
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

def index(request):
    items = Item.objects.all()
    return render(request, "index.html", {"items": items})

def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, "item_detail.html", {"item": item})

def cart(request):
    cart = request.session.get("cart", {})

    # 各アイテムの小計を計算
    for item_id, item in cart.items():
        item["subtotal"] = item["price"] * item["quantity"]
    total_price = sum(item["price"] * item["quantity"] for item in cart.values())

    return render(request, "cart.html", {"cart": cart, "total_price": total_price})

def add_to_cart(request, item_id):

# 辞書型の中の辞書の構造になっている。例が下
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

    # withの中でエラーが発生すると、すべての処理がキャンセルされ、データベースは元の状態に戻る
    try:
        with transaction.atomic():
            if item.stock <= 0:
                return redirect("item_detail", item_id=item.id)
            
            cart = request.session.get("cart", {})

            if str(item_id) in cart:
                cart[str(item_id)]["quantity"] += 1
            
            else:
                cart[str(item_id)] = {"name": item.name, "price": item.price, "quantity": 1}
            
            # セッションを更新
            request.session["cart"] = cart

            return redirect("cart")
    
    except Exception as e:
        print("エラー:", e)
        return redirect("item_detail", item_id=item.id)
    
