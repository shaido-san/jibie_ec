from django.urls import path
from .import views

urlpatterns = [
    path("index", views.index, name="index"),
    path("item/<int:item_id>/", views.item_detail, name="item_detail"),
]