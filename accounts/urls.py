from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import EmailLoginForm
from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "giris/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=EmailLoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "cikis/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("kayit/", views.register, name="register"),
    path("siparislerim/", views.orders, name="orders"),
    path("siparislerim/<str:order_number>/", views.order_detail, name="order_detail"),
    path("siparislerim/<str:order_number>/iptal/", views.order_cancel, name="order_cancel"),
    path("favorilerim/", views.favorites, name="favorites"),
    path("favori/<int:product_id>/", views.favorite_toggle, name="favorite_toggle"),
    path("bilgilerim/", views.profile, name="profile"),
]
