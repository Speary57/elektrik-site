"""Ürün stok değişimlerine bağlı otomatik e-postalar.

1) Stok 0 (veya altı) iken pozitife geçtiğinde: o ürün için bekleyen
   'stok gelince haber ver' taleplerine müşteri bildirimi gönderilir.
2) Stok, eşik değerin (LOW_STOCK_THRESHOLD, varsayılan 3) altına ilk kez
   düştüğünde: işletmeye düşük stok uyarısı gönderilir.

Hem admin liste ekranı (hızlı stok düzenleme) hem de ürün düzenleme formu
üzerinden yapılan değişiklikler yakalanır. Eski stok değeri tek bir yerde
okunduğu için iki mantık tek alıcıda birleştirilmiştir.
"""

import logging

from django.conf import settings
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Product

logger = logging.getLogger("cart.emails")


@receiver(post_init, sender=Product)
def _remember_stock(sender, instance, **kwargs):
    instance._original_stock = instance.stock_quantity
    instance._original_price = instance.price


def _product_url(instance):
    base = getattr(settings, "SITE_URL", "").rstrip("/")
    try:
        return base + instance.get_absolute_url() if base else ""
    except Exception:
        return ""


def _handle_back_in_stock(instance, old_stock, new_stock, product_url):
    if not (old_stock <= 0 and new_stock > 0):
        return
    pending = instance.stock_notifications.filter(notified=False)
    if not pending.exists():
        return

    from cart import emails as order_emails

    count = 0
    for req in list(pending):
        order_emails.send_back_in_stock(instance, req.email, product_url)
        count += 1
    pending.update(notified=True, notified_at=timezone.now())
    logger.info(
        "Stok bildirimi: %s ürünü için %s talebe e-posta gönderildi.",
        instance.name,
        count,
    )


def _handle_price_change(instance, created, product_url):
    """Fiyat değişince ürünü favorileyen kullanıcılara bildirim gönderir."""
    if created:
        return
    old_price = getattr(instance, "_original_price", None)
    new_price = instance.price
    if old_price is None or old_price == new_price:
        return

    favorites = (
        instance.favorited_by.select_related("user").all()
    )
    if not favorites:
        return

    from cart import emails as order_emails

    seen = set()
    count = 0
    for fav in favorites:
        user = fav.user
        email = (getattr(user, "email", "") or "").strip()
        if not email or email in seen:
            continue
        seen.add(email)
        order_emails.send_favorite_price_change(
            instance, email, old_price, new_price, product_url
        )
        count += 1
    if count:
        logger.info(
            "Fiyat değişikliği: %s ürünü için %s favori kullanıcıya e-posta gönderildi (%s -> %s).",
            instance.name,
            count,
            old_price,
            new_price,
        )


def _handle_low_stock(instance, old_stock, new_stock, product_url):
    threshold = getattr(settings, "LOW_STOCK_THRESHOLD", 3)
    # Yalnızca eşiğin üstünden altına ilk geçişte uyar (her kayıtta tekrar etmesin).
    if old_stock >= threshold and new_stock < threshold:
        from cart import emails as order_emails

        order_emails.send_low_stock_alert(instance, product_url)
        logger.info(
            "Düşük stok uyarısı: %s (%s adet) işletmeye bildirildi.",
            instance.name,
            new_stock,
        )


@receiver(post_save, sender=Product)
def _on_product_saved(sender, instance, created, **kwargs):
    old_stock = 0 if created else getattr(instance, "_original_stock", 0) or 0
    new_stock = instance.stock_quantity or 0
    product_url = _product_url(instance)

    _handle_back_in_stock(instance, old_stock, new_stock, product_url)
    _handle_low_stock(instance, old_stock, new_stock, product_url)
    _handle_price_change(instance, created, product_url)

    instance._original_stock = new_stock
    instance._original_price = instance.price
