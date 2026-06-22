from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Address, Profile, SavedCard
from catalog.models import Product

from . import cart as cart_service
from . import emails as order_emails
from .forms import CheckoutForm
from .models import Order, OrderItem

LAST_ORDER_SESSION_KEY = "son_siparis_id"


def cart_detail(request):
    adjusted = cart_service.normalize_cart_stocks(request)
    if adjusted:
        messages.info(
            request,
            "Sepetiniz güncel stok bilgisine göre güncellendi (adetler sınırlandı veya stoksuz ürünler çıkarıldı).",
        )
    lines, total = cart_service.get_cart_lines(request)
    return render(request, "cart/cart.html", {"lines": lines, "total": total})


@require_POST
def add_to_cart(request, product_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    cart_service.normalize_cart_stocks(request)
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        qty = int(request.POST.get("adet", 1))
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, min(qty, 99))

    if product.stock_quantity <= 0:
        msg = "Bu ürün şu an stokta değil."
        if is_ajax:
            return JsonResponse(
                {
                    "ok": False,
                    "level": "warning",
                    "message": msg,
                    "count": cart_service.cart_item_count(request),
                }
            )
        messages.warning(request, msg)
        next_url = request.POST.get("next") or product.get_absolute_url()
        return redirect(next_url)

    current = cart_service.get_line_quantity(request, product.id)
    max_total = int(product.stock_quantity)
    allowed_total = max_total
    can_add = max(0, allowed_total - current)
    qty_to_add = min(qty, can_add)

    if qty_to_add <= 0:
        level = "warning"
        msg = "Sepetinizde bu ürün için stokta izin verilen adede ulaştınız."
    else:
        cart_service.add_product(request, product.id, qty_to_add)
        if qty_to_add < qty:
            level = "info"
            msg = f"Stok nedeniyle yalnızca {qty_to_add} adet eklenebildi (stok: {max_total})."
        else:
            level = "success"
            msg = f"{qty_to_add} adet sepete eklendi."

    if is_ajax:
        return JsonResponse(
            {
                "ok": qty_to_add > 0,
                "level": level,
                "message": msg,
                "count": cart_service.cart_item_count(request),
            }
        )

    getattr(messages, level)(request, msg)
    next_url = request.POST.get("next") or product.get_absolute_url()
    return redirect(next_url)


@require_POST
def update_cart(request):
    cart_service.normalize_cart_stocks(request)
    for key, value in request.POST.items():
        if key.startswith("adet_"):
            pid_str = key.removeprefix("adet_")
            try:
                pid = int(pid_str)
                q = int(value)
            except (TypeError, ValueError):
                continue
            try:
                product = Product.objects.get(pk=pid, is_active=True)
            except Product.DoesNotExist:
                cart_service.remove_product(request, pid)
                continue
            cap = min(99, int(product.stock_quantity))
            q = max(0, min(q, cap))
            cart_service.set_quantity(request, pid, q)
    return redirect("cart:detail")


@require_POST
def remove_from_cart(request, product_id):
    cart_service.remove_product(request, product_id)
    return redirect("cart:detail")


@login_required
def checkout(request):
    adjusted = cart_service.normalize_cart_stocks(request)
    if adjusted:
        messages.info(
            request,
            "Sepetiniz güncel stok bilgisine göre güncellendi. Lütfen tutarları kontrol edin.",
        )
    lines, subtotal = cart_service.get_cart_lines(request)
    if not lines:
        messages.info(request, "Ödeme adımına geçmek için sepetinizde ürün olmalı.")
        return redirect("cart:detail")

    total = subtotal

    default_full_name = (request.user.get_full_name() or "").strip()
    try:
        default_phone = request.user.profile.phone or ""
    except Profile.DoesNotExist:
        default_phone = ""

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = _place_order(request, form, lines, subtotal, total)
            if order is None:
                # Stok yetersizliği vb.; cart_detail mesaj gösterip yeniden hizalar.
                return redirect("cart:detail")
            order_emails.send_business_notification(order)
            order_emails.send_customer_confirmation(order)
            request.session[LAST_ORDER_SESSION_KEY] = order.id
            messages.success(
                request,
                f"Ödemeniz alındı. Sipariş numaranız: {order.order_number}",
            )
            return redirect("cart:order_success")
        messages.error(request, "Ödeme tamamlanamadı. Lütfen işaretli alanları kontrol edin.")
    else:
        initial = {
            "full_name": default_full_name,
            "email": request.user.email,
            "phone": default_phone,
        }
        last_address = request.user.addresses.first()
        if last_address is not None:
            initial.update(
                {
                    "full_name": last_address.full_name,
                    "phone": last_address.phone,
                    "city": last_address.city,
                    "district": last_address.district,
                    "address": last_address.address,
                }
            )
        last_card = request.user.cards.first()
        if last_card is not None:
            digits = last_card.digits
            spaced = " ".join(digits[i : i + 4] for i in range(0, len(digits), 4))
            initial.update(
                {
                    "card_name": last_card.card_name,
                    "card_number": spaced,
                    "card_expiry": last_card.card_expiry,
                }
            )
        form = CheckoutForm(initial=initial)

    addresses = list(request.user.addresses.all())
    cards = list(request.user.cards.all())
    context = {
        "form": form,
        "lines": lines,
        "subtotal": subtotal,
        "total": total,
        "addresses": addresses,
        "cards": cards,
        "default_full_name": default_full_name,
        "default_phone": default_phone,
    }
    return render(request, "cart/checkout.html", context)


def _save_address_if_new(user, data):
    """Kullanıcının girdiği teslimat adresini, aynısı kayıtlı değilse kaydeder."""
    exists = user.addresses.filter(
        full_name=data["full_name"],
        phone=data["phone"],
        city=data["city"],
        district=data["district"],
        address=data["address"],
    ).exists()
    if not exists:
        Address.objects.create(
            user=user,
            full_name=data["full_name"],
            phone=data["phone"],
            city=data["city"],
            district=data["district"],
            address=data["address"],
        )


def _save_card_if_new(user, data):
    """Kullanıcının kartını kaydeder. Güvenlik gereği CVC saklanmaz."""
    number = data["card_number"]  # clean_card_number yalnızca rakam döndürür
    exists = user.cards.filter(
        card_number=number,
        card_expiry=data["card_expiry"],
    ).exists()
    if not exists:
        SavedCard.objects.create(
            user=user,
            card_name=data["card_name"],
            card_number=number,
            card_expiry=data["card_expiry"],
        )


@transaction.atomic
def _place_order(request, form, lines, subtotal, total):
    data = form.cleaned_data
    product_ids = [line["product"].id for line in lines]
    locked = {
        p.id: p
        for p in Product.objects.select_for_update().filter(
            id__in=product_ids, is_active=True
        )
    }

    # Sipariş kesinleşmeden stok son kez doğrulanır.
    for line in lines:
        product = locked.get(line["product"].id)
        if product is None or int(product.stock_quantity) < line["quantity"]:
            messages.error(
                request,
                "Bazı ürünlerin stoğu siz ödeme yaparken değişti. Sepetiniz güncellendi.",
            )
            cart_service.normalize_cart_stocks(request)
            return None

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        full_name=data["full_name"],
        email=data["email"],
        phone=data["phone"],
        city=data["city"],
        district=data["district"],
        address=data["address"],
        note=data.get("note", ""),
        subtotal=subtotal,
        total=total,
        status=Order.STATUS_NEW,
        payment_status=Order.PAYMENT_PAID,
        card_last4=data["card_number"][-4:],
    )

    items = []
    for line in lines:
        product = locked[line["product"].id]
        qty = line["quantity"]
        items.append(
            OrderItem(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=qty,
                line_total=product.price * qty,
            )
        )
        product.stock_quantity = int(product.stock_quantity) - qty
        product.save(update_fields=["stock_quantity"])
    OrderItem.objects.bulk_create(items)

    if request.user.is_authenticated and data.get("save_address"):
        _save_address_if_new(request.user, data)

    if request.user.is_authenticated and data.get("save_card"):
        _save_card_if_new(request.user, data)

    cart_service.clear_cart(request)
    return order


@login_required
def order_success(request):
    order_id = request.session.get(LAST_ORDER_SESSION_KEY)
    order = None
    if order_id:
        order = (
            Order.objects.filter(id=order_id).prefetch_related("items").first()
        )
    if order is None:
        messages.info(request, "Görüntülenecek bir sipariş bulunamadı.")
        return redirect("cart:detail")
    return render(request, "cart/order_success.html", {"order": order})
