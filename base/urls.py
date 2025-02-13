from django.urls import path
from .views import(
    register, CustomLoginView, CustomLogoutView, index,
    item_detail, cart, add_to_cart, remove_from_cart, add_address,
    checkout
)

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout", CustomLogoutView.as_view(next_page="login"), name="logout"),
    path("index/", index, name="index"),
    path("item/<int:item_id>/", item_detail, name="item_detail"),
    path("cart/", cart, name="cart"),
    path("cart/add/<int:item_id>/", add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:item_id>/", remove_from_cart, name="remove_from_cart"),
    path("address/add/", add_address, name="add_address"),
    path("checkout", checkout, name="checkout"),
    
]