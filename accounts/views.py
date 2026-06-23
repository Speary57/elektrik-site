import secrets
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product
from cart.models import Order
from cart import emails as order_emails

from .forms import AccountInfoForm, RegisterForm
from .middleware import SESSION_VERIFIED_AT, SESSION_VERIFIED_UID
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


# ----- Yönetim paneli e-posta doğrulaması (2FA) -----

_OTP_HASH = "admin_otp_hash"
_OTP_EXPIRES = "admin_otp_expires"
_OTP_ATTEMPTS = "admin_otp_attempts"
_OTP_UID = "admin_otp_uid"
_OTP_EMAIL = "admin_otp_email"
# Bu doğrulama için en az bir kod gönderildi mi? (Otomatik tekrar göndermeyi engeller.)
_OTP_SENT = "admin_otp_sent"


def _safe_admin_next(value):
    prefix = getattr(settings, "ADMIN_URL_PREFIX", "/yonetim/")
    if value and value.startswith(prefix) and "//" not in value[1:]:
        return value
    return prefix


def _mask_email(email):
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked = local[0] + "*"
    else:
        masked = local[:2] + "*" * (len(local) - 2)
    return f"{masked}@{domain}"


def _send_admin_code(request, user):
    """Yeni bir doğrulama kodu üretir, oturuma (hash) kaydeder ve e-posta gönderir."""
    code = f"{secrets.randbelow(1000000):06d}"
    ttl = getattr(settings, "ADMIN_OTP_CODE_TTL", 600)
    request.session[_OTP_HASH] = make_password(code)
    request.session[_OTP_EXPIRES] = time.time() + ttl
    request.session[_OTP_ATTEMPTS] = 0
    request.session[_OTP_UID] = user.pk
    request.session[_OTP_EMAIL] = user.email
    request.session[_OTP_SENT] = True
    return order_emails.send_admin_verification_code(user, code)


def _admin_verify_context(request, user, next_url):
    email_configured = (
        settings.EMAIL_HOST_USER
        and settings.EMAIL_HOST_PASSWORD
        and settings.EMAIL_BACKEND != "django.core.mail.backends.console.EmailBackend"
    )
    return {
        "masked_email": _mask_email(user.email),
        "next": next_url,
        "email_configured": email_configured,
    }


def _has_valid_pending(request, user):
    if request.session.get(_OTP_UID) != user.pk:
        return False
    if not request.session.get(_OTP_HASH):
        return False
    expires = request.session.get(_OTP_EXPIRES, 0)
    return time.time() < float(expires)


@login_required
def admin_verify(request):
    user = request.user
    next_url = _safe_admin_next(
        request.POST.get("next") or request.GET.get("next")
    )

    if not user.is_staff:
        return redirect("catalog:home")

    if not user.email:
        return render(
            request,
            "registration/admin_verify.html",
            {"no_email": True},
        )

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "resend":
            if _send_admin_code(request, user):
                messages.success(request, "Yeni bir doğrulama kodu e-postanıza gönderildi.")
            else:
                messages.error(
                    request,
                    "Doğrulama kodu gönderilemedi. E-posta ayarlarını kontrol edin "
                    "veya spam klasörüne bakın.",
                )
            return redirect(f"{request.path}?next={next_url}")

        code = (request.POST.get("code") or "").strip()
        if not _has_valid_pending(request, user):
            messages.error(
                request,
                "Kodun süresi doldu. Lütfen “Yeni kod gönder” ile yeni bir kod isteyin.",
            )
            return render(
                request,
                "registration/admin_verify.html",
                _admin_verify_context(request, user, next_url),
            )

        max_attempts = getattr(settings, "ADMIN_OTP_MAX_ATTEMPTS", 5)
        attempts = int(request.session.get(_OTP_ATTEMPTS, 0))
        if check_password(code, request.session.get(_OTP_HASH, "")):
            # Başarılı: panel erişimini aç, bekleyen kodu temizle.
            request.session[SESSION_VERIFIED_AT] = time.time()
            request.session[SESSION_VERIFIED_UID] = user.pk
            for key in (_OTP_HASH, _OTP_EXPIRES, _OTP_ATTEMPTS, _OTP_UID, _OTP_EMAIL, _OTP_SENT):
                request.session.pop(key, None)
            return redirect(next_url)

        attempts += 1
        request.session[_OTP_ATTEMPTS] = attempts
        if attempts >= max_attempts:
            for key in (_OTP_HASH, _OTP_EXPIRES, _OTP_ATTEMPTS):
                request.session.pop(key, None)
            messages.error(
                request,
                "Çok fazla hatalı deneme. Lütfen yeni kod isteyin.",
            )
        else:
            messages.error(
                request,
                f"Kod hatalı. Kalan deneme: {max_attempts - attempts}.",
            )
        return render(
            request,
            "registration/admin_verify.html",
            _admin_verify_context(request, user, next_url),
        )

    # GET: yalnızca bu doğrulama için hiç kod gönderilmediyse ilk kodu gönder.
    # Süre dolduğunda otomatik tekrar gönderim YOK; kullanıcı "Yeni kod gönder"e basmalı.
    if not request.session.get(_OTP_SENT):
        if not _send_admin_code(request, user):
            messages.error(
                request,
                "Doğrulama kodu gönderilemedi. Sunucuda EMAIL_HOST_USER ve "
                "EMAIL_HOST_PASSWORD ayarlı olmalıdır (Gmail uygulama şifresi).",
            )

    return render(
        request,
        "registration/admin_verify.html",
        _admin_verify_context(request, user, next_url),
    )


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
