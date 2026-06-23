from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product
from cart.models import Order
from cart import emails as order_emails

from .forms import AccountInfoForm, RegisterForm
from .models import Favorite, Profile


def register(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Hoş geldiniz {user.first_name or user.email}! Hesabınız oluşturuldu.",
            )
            return redirect("catalog:home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def orders(request):
    order_list = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )
    return render(request, "accounts/orders.html", {"orders": order_list})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        order_number=order_number,
        user=request.user,
    )
    return render(request, "accounts/order_detail.html", {"order": order})


@require_POST
@login_required
def order_cancel(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        order_number=order_number,
        user=request.user,
    )
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if order.can_cancel:
        with transaction.atomic():
            order.status = Order.STATUS_CANCELLED_BY_USER
            order.save(update_fields=["status"])
            # Stok geri yükleme cart.signals üzerinden otomatik yapılır.
        # İşletmeye iptal bildirimi (arka planda gönderilir).
        order_emails.send_business_cancellation(order)
        level = "success"
        msg = "Siparişiniz iptal edildi ve ürünler stoğa geri eklendi."
    else:
        level = "info"
        msg = "Bu sipariş artık iptal edilemez."

    if is_ajax:
        return JsonResponse(
            {
                "ok": level == "success",
                "level": level,
                "message": msg,
                "status_code": order.status,
                "status_display": order.get_status_display(),
            }
        )

    getattr(messages, level)(request, msg)
    return redirect("accounts:order_detail", order_number=order.order_number)


@login_required
def favorites(request):
    favorite_qs = (
        Favorite.objects.filter(user=request.user)
        .select_related("product", "product__category")
        .order_by("-created_at")
    )
    products = [f.product for f in favorite_qs if f.product and f.product.is_active]
    favorite_ids = {p.id for p in products}
    return render(
        request,
        "accounts/favorites.html",
        {"products": products, "favorite_ids": favorite_ids},
    )


@require_POST
@login_required
def favorite_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user, product=product
    )
    if created:
        active = True
    else:
        favorite.delete()
        active = False

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        count = Favorite.objects.filter(user=request.user).count()
        return JsonResponse({"active": active, "count": count})

    messages.success(
        request,
        "Ürün favorilere eklendi." if active else "Ürün favorilerden çıkarıldı.",
    )
    next_url = request.POST.get("next") or "catalog:home"
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect(next_url)


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = AccountInfoForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Bilgileriniz güncellendi.")
            return redirect("accounts:profile")
        messages.error(request, "Bilgiler güncellenemedi. Lütfen alanları kontrol edin.")
    else:
        form = AccountInfoForm(
            user=request.user,
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "phone": profile_obj.phone,
                "birth_date": profile_obj.birth_date,
            },
        )
    return render(request, "accounts/profile.html", {"form": form})
