import stripe
from django.conf import settings
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
def checkout(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)

    # カートが空ならcart.htmlにリダイレクト
    if not cart_items.exists():
        messages.error(request, "カートは空です")
        return redirect("cart")
    
    # ユーザーの登録済み住所
    addresses = Address.objects.filter(user=user)  
    total_price = 0
    for cart_item in cart_items:
        item_price = cart_item.item.tax_price()  # 税込み価格を取得
        item_quantity = cart_item.quantity  # カート内の個数
        subtotal = item_price * item_quantity  # 小計
        total_price += subtotal  # 合計金額を加算
    

    if request.method == "POST":
        address_id = request.POST.get("address_id")

        # 住所が選択されているかチェック
        if not address_id:
            messages.error(request, "送付先の住所を選択してください")
            return render(request, "checkout.html", {"cart_items": cart_items, "addresses": addresses, "total_price": total_price})

        address = get_object_or_404(Address, id=address_id, user=user)
        total_price = 0
        for cart_item in cart_items:
            item_price = cart_item.item.tax_price()  # 税込み価格を取得
            item_quantity = cart_item.quantity  # カート内の個数
            subtotal = item_price * item_quantity  # 小計
            total_price += subtotal  # 合計金額を加算

        # 在庫をチェックして、ないまたは足りない場合削除。在庫の確保はしない。
        # 決済するときに在庫をもう一度チェックする。
        not_stock_items = []
        for cart_item in cart_items:
            stock_entry = Stock.objects.get(item=cart_item.item)

            # カート商品の個数と在庫の個数を比較して、足りなかったら削除する商品リストに入れる。
            if stock_entry.quantity < cart_item.quantity:
                not_stock_items.append(cart_item)
        
        # 削除する商品リストがあるなら削除する。その後、カートにリダイレクト。
        if not_stock_items:
            for item in not_stock_items:
                item.delete()
            
            messages.error(request, "在庫が足りない商品があったので、もう一度やり直してください。")
            return redirect("cart")
        
        # 住所がチェックされていたら決済ページを作成し、決済する画面へ。また、在庫のチェックはその時行うようにする。
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "jpy",
                        "product_data": {
                            "name": cart_item.item.name,
                        },
                        "unit_amount": cart_item.item.tax_price(),
                    },
                    "quantity": cart_item.quantity,
                }
                for cart_item in cart_items
            ],
            mode="payment",
            success_url=request.build_absolute_uri(f"/success/?address_id={address.id}"),
            cancel_url=request.build_absolute_uri("/checkout/")
        )

        return redirect(session.url, code=303)
    
    return render(request, "checkout.html", {"cart_items": cart_items, "addresses": addresses, "total_price": total_price})

@login_required
def success(request):
    user = request.user
    address_id = request.GET.get("address_id")
    
    # 住所がない場合はエラーを出す
    if not address_id:
        messages.error(request, "住所を指定してください。")
        return redirect("cart")
    
    address = get_object_or_404(Address, id=address_id, user=user)
    cart_items = Cart.objects.filter(user=user)

    # カートが空ならリダイレクト
    if not cart_items.exists():
        messages.error(request, "カートはからです")
        return redirect("cart")
    
    total_price = 0

    for cart_item in cart_items:
        item_price = cart_item.item.tax_price()
        item_quantity = cart_item.quantity
        subtotal = item_price * item_quantity
        total_price += subtotal
    
    not_stock_items = []
    for cart_item in cart_items:
        stock_entry = Stock.objects.get(item=cart_item.item)
        if stock_entry.quantity < cart_item.quantity:
            not_stock_items.append(cart_item)
    
    if not_stock_items:
        messages.error(request, "在庫不足です。やり直しをお願いします。")
        return redirect("cart")
    
    # 注文を確定する。注文ーブルを作り、在庫を減らす処理。
    with transaction.atomic():
        order = Order.objects.create(user=user, address=address, total_price=total_price)

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                item=cart_item.item,
                quantity=cart_item.quantity,
                subtotal_price=cart_item.item.tax_price() * cart_item.quantity
            )

            # ここで在庫を減らす。
            stock_entry = Stock.objects.get(item=cart_item.item)
            stock_entry.quantity -= cart_item.quantity
            stock_entry.save()
        
        # 注文を確定後にカートの中身を削除する。逆ではダメ
        cart_items.delete()
    
    messages.success(request, "ご注文ありがとうございます。注文が確定しました。")
    return render(request, "success.html",{"order":order})

@login_required
def add_address(request):
    user = request.user

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
            messages.success(request, "住所登録しました")
            return redirect("checkout")
    
    else:
        form = AddressForm()
    
    return render(request, "add_address.html", {"form": form})

@login_required
def order_history(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by("-created_at")
    return render(request, "order_history.html", {"orders": orders})

