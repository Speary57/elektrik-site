from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("iletisim/gonder/", views.contact_submit, name="contact_submit"),
    path("iletisim/", views.contact, name="contact"),
    path("hakkimizda/", views.about, name="about"),
    path("urunler/", views.product_list, name="product_list"),
    path("stok-bildirim/<int:product_id>/", views.stock_notify, name="stock_notify"),
    # slug: yalnızca ASCII; Türkçe ürün adlarından gelen Unicode slug için str kullanılıyor
    path("urunler/<str:slug>/", views.product_detail, name="product_detail"),
]
