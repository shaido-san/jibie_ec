from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, AddressForm
from .models import Item, Cart, Stock, Order, OrderItem, Address
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
    stock_item_range = range(1, item.get_stock() + 1)
    return render(request, "item_detail.html", {"item": item, "stock_item_range":stock_item_range})

@login_required
def cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)

    total_price = 0
    cart_data = []

    for cart_item in cart_items:
        image_url = cart_item.item.image.url if cart_item.item.image else None
        subtotal = cart_item.item.tax_price() * cart_item.quantity
        total_price += subtotal
        cart_data.append({
            "item":cart_item.item,
            "image_url": image_url,
            "quantity": cart_item.quantity,
            "subtotal": subtotal
        })
    return render(request, "cart.html", {"cart": cart_data, "total_price":total_price})

@login_required   
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

        # 現在の在庫数をStockテーブルから取得
        stock_entry = Stock.objects.filter(item=item).first()
        available_stock = stock_entry.quantity if stock_entry else 0        

        # 現在のカート内商品の個数を取得
        cart_item, created = Cart.objects.get_or_create(user=user, item=item, defaults={"quantity": 0})
        current_cart_quantity = cart_item.quantity

        if current_cart_quantity + quantity > available_stock:
            messages.error(request, "在庫不足です。もう一度やり直してください。")
            return redirect("item_detail", item_id=item.id)
        
        with transaction.atomic():
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, "カートに商品を追加しました！")
        return redirect("cart")
    
    return redirect("item_detail", item_id=item.id)

@login_required
def remove_from_cart(request, item_id):
    user= request.user
    cart_item = get_object_or_404(Cart, user=user, item_id=item_id)

    with transaction.atomic():
        cart_item.delete()
    
    messages.success(request, "カートから商品を削除しました")
    return redirect("cart")

@login_required
def add_address(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "住所を登録しました。")
            return redirect("checkout")
        
        else:
            form = AddressForm()
        
        return render(request, "add_address.html", {"form": form})

@login_required
@login_required
def checkout(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)

    # カートが空ならリダイレクト
    if not cart_items.exists():
        messages.error(request, "カートは空です")
        return redirect("cart")

    addresses = Address.objects.filter(user=user)  # ユーザーの登録済み住所

    total_price = sum(cart_item.item.tax_price() * cart_item.quantity for cart_item in cart_items)

    if request.method == "POST":
        address_id = request.POST.get("address_id")

        # 住所が選択されているかチェック
        if not address_id:
            messages.error(request, "送付先の住所を選択してください")
            return render(request, "checkout.html", {"cart_items": cart_items, "addresses": addresses, "total_price": total_price})

        address = get_object_or_404(Address, id=address_id, user=user)

        # ✅ 注文確定処理
        with transaction.atomic():
            order = Order.objects.create(user=user, address=address, total_price=total_price)

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    item=cart_item.item,
                    quantity=cart_item.quantity,
                    subtotal_price=cart_item.item.tax_price() * cart_item.quantity
                )

            cart_items.delete()  # ✅ カートの中身を削除

        messages.success(request, "注文が確定しました")
        return redirect("index")

    return render(request, "checkout.html", {"cart_items": cart_items, "addresses": addresses, "total_price": total_price})

@login_required
def add_address(request):
    user = request.user
    address = Address.objects.filter(user=user)

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
            messages.success(request, "住所登録しました")
            return redirect("add_address")
    
    else:
        form = AddressForm()
    
    return render(request, "add_address.html")