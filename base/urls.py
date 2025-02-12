from django.urls import path
from .import views 
# views.pyにあるそれぞれのカスタムクラスをインポートしている
from .views import register, CustomLoginView, CustomLogoutView


urlpatterns = [
    path("register/", register, name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout", CustomLogoutView.as_view(next_page="login"), name="logout"),
    path("index/", views.index, name="index"),
    path("item/<int:item_id>/", views.item_detail, name="item_detail"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:item_id>/", views.add_to_cart, name="add_to_cart"),
    
]