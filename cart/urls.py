from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="detail"),
    path("ekle/<int:product_id>/", views.add_to_cart, name="add"),
    path("guncelle/", views.update_cart, name="update"),
    path("kaldir/<int:product_id>/", views.remove_from_cart, name="remove"),
    path("odeme/", views.checkout, name="checkout"),
    path("siparis-alindi/", views.order_success, name="order_success"),
]
