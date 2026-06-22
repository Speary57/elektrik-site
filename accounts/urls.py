from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import AsyncPasswordResetForm, EmailLoginForm, StyledSetPasswordForm
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
    path(
        "parola-sifirla/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            html_email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            form_class=AsyncPasswordResetForm,
            success_url="/hesap/parola-sifirla/gonderildi/",
        ),
        name="password_reset",
    ),
    path(
        "parola-sifirla/gonderildi/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "parola-yenile/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            form_class=StyledSetPasswordForm,
            success_url="/hesap/parola-yenile/tamam/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "parola-yenile/tamam/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("siparislerim/", views.orders, name="orders"),
    path("siparislerim/<str:order_number>/", views.order_detail, name="order_detail"),
    path("siparislerim/<str:order_number>/iptal/", views.order_cancel, name="order_cancel"),
    path("favorilerim/", views.favorites, name="favorites"),
    path("favori/<int:product_id>/", views.favorite_toggle, name="favorite_toggle"),
    path("bilgilerim/", views.profile, name="profile"),
    path("yonetim-dogrulama/", views.admin_verify, name="admin_verify"),
]
