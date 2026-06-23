"""Sipariş ve hesap e-postaları — işletme bildirimi, müşteri onayı, durum güncellemesi.

E-postalar hem düz metin hem de profesyonel HTML (kalın başlıklar, düzenli tablo)
biçiminde gönderilir. Gönderimler arka planda (ayrı iş parçacığı) yapılır; akış
SMTP'yi beklemez.
"""

import logging
import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger("cart.emails")

BRAND = "Kılağuz Elektrik ve Yapı Market"
BRAND_COLOR = "#2563eb"


def _send_sync(subject, text_body, html_body, recipients):
    """Kritik e-postalar (doğrulama kodu vb.) için senkron gönderim."""
    recipients = [r for r in recipients if r]
    if not recipients:
        return False
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=recipients,
        )
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("E-posta gönderildi -> %s | %s", recipients, subject)
        return True
    except Exception:
        logger.exception("E-posta gönderilemedi -> %s | %s", recipients, subject)
        return False


def _send_async(subject, text_body, html_body, recipients,
                attachments=None, attachment_factory=None):
    """E-postayı arka planda gönderir.

    attachment_factory: argümansız çağrılan, [(ad, içerik, mimetype), ...] döndüren
    bir fonksiyon olabilir. Ağır ek üretimi (ör. PDF) isteğin ana akışını değil bu
    arka plan iş parçacığını yavaşlatır.
    """
    recipients = [r for r in recipients if r]
    if not recipients:
        return
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

    def _run():
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=recipients,
            )
            if html_body:
                msg.attach_alternative(html_body, "text/html")
            all_attachments = list(attachments or [])
            if attachment_factory is not None:
                try:
                    all_attachments += list(attachment_factory() or [])
                except Exception:
                    logger.exception("E-posta eki üretilemedi (atlanıyor).")
            for filename, content, mimetype in all_attachments:
                msg.attach(filename, content, mimetype)
            # fail_silently=False: hata olursa aşağıdaki except yakalayıp loglar.
            msg.send(fail_silently=False)
            logger.info("E-posta gönderildi -> %s | %s", recipients, subject)
        except Exception:
            # Hata ana akışı durdurmamalı; ama sunucu terminaline loglanır.
            logger.exception("E-posta gönderilemedi -> %s | %s", recipients, subject)

    threading.Thread(target=_run, daemon=True).start()


def _html_shell(title, intro, inner=""):
    """Tüm maillerde ortak, profesyonel HTML iskeleti (kalın başlıklar dâhil)."""
    return f"""\
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 6px 24px rgba(15,23,42,0.08);font-family:Arial,Helvetica,sans-serif;">
        <tr>
          <td style="background:{BRAND_COLOR};padding:22px 28px;">
            <span style="display:block;color:#ffffff;font-size:18px;font-weight:bold;letter-spacing:0.2px;">{BRAND}</span>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <h1 style="margin:0 0 14px;font-size:20px;font-weight:bold;color:#0f172a;">{title}</h1>
            <p style="margin:0 0 20px;font-size:15px;font-weight:bold;color:#1e293b;line-height:1.6;">{intro}</p>
            {inner}
          </td>
        </tr>
        <tr>
          <td style="padding:18px 28px;background:#f8fafc;border-top:1px solid #e2e8f0;">
            <p style="margin:0;font-size:12px;color:#64748b;line-height:1.5;">
              Bu e-posta <strong style="color:#475569;">{BRAND}</strong> tarafından otomatik olarak gönderilmiştir.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _info_table(rows):
    """[(etiket, değer)] -> kalın etiketli bilgi tablosu (HTML)."""
    cells = ""
    for label, value in rows:
        cells += (
            f'<tr>'
            f'<td style="padding:7px 0;font-size:14px;font-weight:bold;color:#475569;width:42%;vertical-align:top;">{label}</td>'
            f'<td style="padding:7px 0;font-size:14px;color:#0f172a;font-weight:bold;">{value}</td>'
            f"</tr>"
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-collapse:collapse;margin:0 0 18px;">'
        f"{cells}</table>"
    )


def _items_table(order):
    rows = ""
    for it in order.items.all():
        rows += (
            f'<tr>'
            f'<td style="padding:8px 0;font-size:14px;font-weight:bold;color:#0f172a;border-bottom:1px solid #eef2f7;">{it.product_name}</td>'
            f'<td style="padding:8px 0;font-size:14px;font-weight:bold;color:#475569;text-align:center;border-bottom:1px solid #eef2f7;">{it.quantity} ad.</td>'
            f'<td style="padding:8px 0;font-size:14px;font-weight:bold;color:#0f172a;text-align:right;border-bottom:1px solid #eef2f7;">{it.line_total} TL</td>'
            f"</tr>"
        )
    head = (
        '<tr>'
        '<th align="left" style="padding:6px 0;font-size:12px;font-weight:bold;color:#94a3b8;text-transform:uppercase;letter-spacing:0.4px;">Ürün</th>'
        '<th align="center" style="padding:6px 0;font-size:12px;font-weight:bold;color:#94a3b8;text-transform:uppercase;letter-spacing:0.4px;">Adet</th>'
        '<th align="right" style="padding:6px 0;font-size:12px;font-weight:bold;color:#94a3b8;text-transform:uppercase;letter-spacing:0.4px;">Tutar</th>'
        "</tr>"
    )
    total = (
        f'<tr>'
        f'<td colspan="2" style="padding:12px 0 0;font-size:15px;font-weight:bold;color:#0f172a;">Genel toplam</td>'
        f'<td style="padding:12px 0 0;font-size:16px;font-weight:bold;color:{BRAND_COLOR};text-align:right;">{order.total} TL</td>'
        f"</tr>"
    )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-collapse:collapse;margin:0 0 18px;">'
        f"{head}{rows}{total}</table>"
    )


def _section_title(text):
    return (
        f'<p style="margin:22px 0 8px;font-size:13px;font-weight:bold;color:{BRAND_COLOR};'
        f'text-transform:uppercase;letter-spacing:0.6px;">{text}</p>'
    )


def _delivery_html(order):
    note = ""
    if order.note:
        note = (
            f'<p style="margin:8px 0 0;font-size:14px;color:#0f172a;font-weight:bold;">'
            f'<span style="color:#475569;">Sipariş notu:</span> {order.note}</p>'
        )
    return (
        f'<p style="margin:0;font-size:14px;font-weight:bold;color:#0f172a;line-height:1.6;">'
        f"{order.district} / {order.city}<br>{order.address}</p>{note}"
    )


# ----- Düz metin yardımcıları (HTML görüntülenemezse) -----

def _items_text(order):
    return "\n".join(
        f"  - {it.product_name} x {it.quantity} = {it.line_total} TL"
        for it in order.items.all()
    )


def _delivery_text(order):
    block = f"TESLİMAT ADRESİ\n  {order.district} / {order.city}\n  {order.address}\n"
    if order.note:
        block += f"\nSipariş notu: {order.note}\n"
    return block


def send_business_notification(order):
    """Yeni sipariş geldiğinde işletme e-postasına ayrıntılı bildirim."""
    recipient = getattr(settings, "ORDER_NOTIFICATION_EMAIL", "")
    if not recipient:
        return
    created_local = timezone.localtime(order.created_at)
    subject = f"Yeni sipariş: {order.order_number} — {order.full_name}"

    text_body = (
        f"Yeni bir sipariş alındı.\n\n"
        f"Sipariş No: {order.order_number}\n"
        f"Tarih: {created_local:%d.%m.%Y %H:%M}\n"
        f"Durum: {order.get_status_display()}\n"
        f"Ödeme: {order.get_payment_status_display()}\n\n"
        f"MÜŞTERİ\n"
        f"  Ad soyad: {order.full_name}\n"
        f"  E-posta: {order.email}\n"
        f"  Telefon: {order.phone}\n\n"
        f"{_delivery_text(order)}"
        f"\nÜRÜNLER\n{_items_text(order)}\n\n"
        f"Ara toplam: {order.subtotal} TL\n"
        f"Genel toplam: {order.total} TL\n"
    )

    inner = (
        _info_table(
            [
                ("Sipariş No", order.order_number),
                ("Tarih", f"{created_local:%d.%m.%Y %H:%M}"),
                ("Durum", order.get_status_display()),
                ("Ödeme", order.get_payment_status_display()),
            ]
        )
        + _section_title("Müşteri")
        + _info_table(
            [
                ("Ad soyad", order.full_name),
                ("E-posta", order.email),
                ("Telefon", order.phone),
            ]
        )
        + _section_title("Teslimat adresi")
        + _delivery_html(order)
        + _section_title("Ürünler")
        + _items_table(order)
    )
    html_body = _html_shell(
        "Yeni sipariş alındı",
        "Mağazanıza yeni bir sipariş ulaştı. Ayrıntılar aşağıdadır.",
        inner,
    )
    _send_async(subject, text_body, html_body, [recipient])


def send_business_cancellation(order):
    """Kullanıcı siparişini iptal ettiğinde işletme e-postasına bildirim."""
    recipient = getattr(settings, "ORDER_NOTIFICATION_EMAIL", "")
    if not recipient:
        return
    created_local = timezone.localtime(order.created_at)
    subject = f"Sipariş iptal edildi: {order.order_number} — {order.full_name}"

    text_body = (
        f"Bir müşteri siparişini iptal etti.\n\n"
        f"Sipariş No: {order.order_number}\n"
        f"Sipariş tarihi: {created_local:%d.%m.%Y %H:%M}\n"
        f"Güncel durum: {order.get_status_display()}\n\n"
        f"MÜŞTERİ\n"
        f"  Ad soyad: {order.full_name}\n"
        f"  E-posta: {order.email}\n"
        f"  Telefon: {order.phone}\n\n"
        f"{_delivery_text(order)}"
        f"\nİPTAL EDİLEN ÜRÜNLER\n{_items_text(order)}\n\n"
        f"Genel toplam: {order.total} TL\n\n"
        f"Not: İptal edilen ürünler otomatik olarak stoğa geri eklenmiştir.\n"
    )

    inner = (
        _info_table(
            [
                ("Sipariş No", order.order_number),
                ("Sipariş tarihi", f"{created_local:%d.%m.%Y %H:%M}"),
                ("Güncel durum", order.get_status_display()),
            ]
        )
        + _section_title("Müşteri")
        + _info_table(
            [
                ("Ad soyad", order.full_name),
                ("E-posta", order.email),
                ("Telefon", order.phone),
            ]
        )
        + _section_title("Teslimat adresi")
        + _delivery_html(order)
        + _section_title("İptal edilen ürünler")
        + _items_table(order)
        + '<p style="margin:18px 0 0;font-size:13px;font-weight:bold;color:#92400e;'
        'background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;padding:12px 14px;line-height:1.6;">'
        "İptal edilen ürünler otomatik olarak stoğa geri eklenmiştir.</p>"
    )
    html_body = _html_shell(
        "Sipariş iptal edildi",
        "Bir müşteri siparişini iptal etti. Ayrıntılar aşağıdadır.",
        inner,
    )
    _send_async(subject, text_body, html_body, [recipient])


def send_customer_confirmation(order):
    """Sipariş veren müşteriye sipariş onayı / özeti."""
    if not order.email:
        return
    first_name = (order.full_name or "").split(" ")[0] if order.full_name else ""
    greeting = f"Merhaba {first_name}," if first_name else "Merhaba,"
    subject = f"Siparişiniz alındı — {order.order_number}"

    text_body = (
        f"{greeting}\n\n"
        f"Siparişinizi aldık, teşekkür ederiz! Sipariş özetiniz aşağıdadır.\n\n"
        f"Sipariş No: {order.order_number}\n"
        f"Durum: {order.get_status_display()}\n\n"
        f"ÜRÜNLER\n{_items_text(order)}\n\n"
        f"Genel toplam: {order.total} TL\n\n"
        f"{_delivery_text(order)}"
        f"\nSiparişinizin durumunu hesabınızdaki 'Tüm siparişlerim' bölümünden "
        f"takip edebilirsiniz.\n\n{BRAND}"
    )

    inner = (
        _info_table(
            [
                ("Sipariş No", order.order_number),
                ("Durum", order.get_status_display()),
            ]
        )
        + _section_title("Ürünler")
        + _items_table(order)
        + _section_title("Teslimat adresi")
        + _delivery_html(order)
        + f'<p style="margin:22px 0 0;font-size:14px;font-weight:bold;color:#1e293b;line-height:1.6;">'
        f"Siparişinizin durumunu hesabınızdaki <strong>“Tüm siparişlerim”</strong> "
        f"bölümünden takip edebilirsiniz.</p>"
    )
    html_body = _html_shell(
        "Siparişiniz alındı",
        f"{greeting} siparişinizi aldık, teşekkür ederiz! Sipariş özetiniz aşağıdadır.",
        inner,
    )

    # PDF fatura, gönderim sırasında arka planda üretilir (ana akışı yavaşlatmaz).
    # reportlab yoksa veya hata olursa fatura eki olmadan gönderilir.
    def _invoice_attachment():
        from .invoices import build_invoice_pdf

        pdf = build_invoice_pdf(order)
        if pdf:
            return [(f"Fatura-{order.order_number}.pdf", pdf, "application/pdf")]
        return []

    _send_async(
        subject, text_body, html_body, [order.email],
        attachment_factory=_invoice_attachment,
    )


def send_admin_verification_code(user, code):
    """Yönetim paneline girişte personel kullanıcıya e-posta doğrulama kodu."""
    email = getattr(user, "email", "")
    if not email:
        return False
    name = (user.get_full_name() or user.get_username() or "").strip()
    greeting = f"Merhaba {name}," if name else "Merhaba,"
    subject = f"Yönetim paneli doğrulama kodu: {code}"

    text_body = (
        f"{greeting}\n\n"
        "Yönetim paneline giriş için doğrulama kodunuz:\n\n"
        f"    {code}\n\n"
        "Bu kod 10 dakika boyunca geçerlidir. Bu isteği siz yapmadıysanız "
        "hesabınızın parolasını değiştirin.\n\n"
        f"{BRAND}"
    )

    inner = (
        '<p style="margin:0 0 10px;font-size:14px;font-weight:bold;color:#475569;">'
        "Yönetim paneline giriş doğrulama kodunuz:</p>"
        f'<div style="margin:0 0 18px;text-align:center;">'
        f'<span style="display:inline-block;font-size:30px;font-weight:bold;'
        f"letter-spacing:8px;color:{BRAND_COLOR};background:#eff6ff;"
        f'border:1px solid #bfdbfe;border-radius:12px;padding:14px 26px;">{code}</span>'
        "</div>"
        '<p style="margin:0;font-size:13px;font-weight:bold;color:#92400e;'
        "background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;"
        'padding:12px 14px;line-height:1.6;">'
        "Bu kod <strong>10 dakika</strong> geçerlidir. İsteği siz yapmadıysanız "
        "lütfen hesap parolanızı değiştirin.</p>"
    )
    html_body = _html_shell(
        "Yönetim paneli doğrulama",
        f"{greeting} yönetim paneline güvenli giriş için doğrulama kodunuzu aşağıda bulabilirsiniz.",
        inner,
    )
    # Render/gunicorn ortamında arka plan iş parçacığı istek bitmeden sonlanabiliyor.
    return _send_sync(subject, text_body, html_body, [email])


def send_low_stock_alert(product, product_url=""):
    """Ürün stoğu eşik değerin altına düşünce işletmeye uyarı maili."""
    recipient = getattr(settings, "ORDER_NOTIFICATION_EMAIL", "")
    if not recipient:
        return
    stock = int(product.stock_quantity)
    state = "TÜKENDİ" if stock <= 0 else f"{stock} adet kaldı"
    subject = f"Stok uyarısı: {product.name} — {state}"

    text_body = (
        "Stok uyarısı!\n\n"
        f"Aşağıdaki ürünün stoğu azaldı, yeniden tedarik gerekebilir.\n\n"
        f"Ürün: {product.name}\n"
        f"Kategori: {product.category.name}\n"
        f"Kalan stok: {stock} adet\n"
        f"Fiyat: {product.price} TL\n\n"
        + (f"Ürün sayfası: {product_url}\n\n" if product_url else "")
        + f"{BRAND}"
    )

    badge_color = "#b91c1c" if stock <= 0 else "#b45309"
    badge_bg = "#fee2e2" if stock <= 0 else "#fef3c7"
    badge_border = "#fca5a5" if stock <= 0 else "#fcd34d"

    button = ""
    if product_url:
        button = (
            f'<p style="margin:22px 0 0;">'
            f'<a href="{product_url}" '
            f'style="display:inline-block;background:{BRAND_COLOR};color:#ffffff;'
            f'font-size:15px;font-weight:bold;text-decoration:none;padding:12px 22px;'
            f'border-radius:10px;">Ürünü yönet</a></p>'
        )

    inner = (
        f'<p style="margin:0 0 18px;">'
        f'<span style="display:inline-block;font-size:14px;font-weight:bold;'
        f'color:{badge_color};background:{badge_bg};border:1px solid {badge_border};'
        f'border-radius:999px;padding:6px 14px;">Kalan stok: {state}</span></p>'
        + _info_table(
            [
                ("Ürün", product.name),
                ("Kategori", product.category.name),
                ("Kalan stok", f"{stock} adet"),
                ("Fiyat", f"{product.price} TL"),
            ]
        )
        + '<p style="margin:18px 0 0;font-size:14px;font-weight:bold;color:#1e293b;'
        'line-height:1.6;">Satışların aksamaması için ürünü yeniden tedarik etmeniz '
        "önerilir.</p>"
        + button
    )
    html_body = _html_shell(
        "Stok azaldı uyarısı",
        f"<strong>{product.name}</strong> ürününün stoğu azaldı. Ayrıntılar aşağıdadır.",
        inner,
    )
    _send_async(subject, text_body, html_body, [recipient])


def send_back_in_stock(product, email, product_url=""):
    """Stok talebi olan ürün yeniden stoğa girince müşteriye bildirim."""
    if not email:
        return
    subject = f"Tekrar stokta: {product.name}"

    text_body = (
        "Merhaba,\n\n"
        f"Haberiniz olsun! Beklediğiniz ürün yeniden stoğa girdi:\n\n"
        f"{product.name}\n"
        f"Fiyat: {product.price} TL\n\n"
        + (f"Ürünü incelemek için: {product_url}\n\n" if product_url else "")
        + "Stoklarla sınırlıdır; sipariş vermek için acele etmenizi öneririz.\n\n"
        f"{BRAND}"
    )

    button = ""
    if product_url:
        button = (
            f'<p style="margin:22px 0 0;">'
            f'<a href="{product_url}" '
            f'style="display:inline-block;background:{BRAND_COLOR};color:#ffffff;'
            f'font-size:15px;font-weight:bold;text-decoration:none;padding:12px 22px;'
            f'border-radius:10px;">Ürünü incele ve sipariş ver</a></p>'
        )

    inner = (
        _info_table(
            [
                ("Ürün", product.name),
                ("Fiyat", f"{product.price} TL"),
            ]
        )
        + '<p style="margin:18px 0 0;font-size:14px;font-weight:bold;color:#1e293b;'
        'line-height:1.6;">Stoklarla sınırlıdır; sipariş vermek için acele etmenizi '
        "öneririz.</p>"
        + button
    )
    html_body = _html_shell(
        "Beklediğiniz ürün tekrar stokta!",
        f"<strong>{product.name}</strong> yeniden satışta. Kaçırmadan sipariş verebilirsiniz.",
        inner,
    )
    _send_async(subject, text_body, html_body, [email])


def send_favorite_price_change(product, email, old_price, new_price, product_url=""):
    """Favorilere eklenmiş bir ürünün fiyatı değişince ilgili kullanıcıya bildirim."""
    if not email:
        return

    try:
        dropped = new_price < old_price
    except TypeError:
        dropped = False

    if dropped:
        headline = "Favori ürününüzün fiyatı düştü!"
        intro = (
            f"<strong>{product.name}</strong> ürününün fiyatı düştü. "
            "Kaçırmadan inceleyebilirsiniz."
        )
        badge_color, badge_bg, badge_border = "#047857", "#d1fae5", "#6ee7b7"
        badge_text = "Fiyat düştü"
    else:
        headline = "Favori ürününüzün fiyatı güncellendi"
        intro = (
            f"<strong>{product.name}</strong> ürününün fiyatı güncellendi. "
            "Güncel fiyatı aşağıda bulabilirsiniz."
        )
        badge_color, badge_bg, badge_border = "#b45309", "#fef3c7", "#fcd34d"
        badge_text = "Fiyat güncellendi"

    subject = f"Favori ürününüzde fiyat değişikliği: {product.name}"

    text_body = (
        "Merhaba,\n\n"
        f"Favorilerinize eklediğiniz bir ürünün fiyatı değişti:\n\n"
        f"{product.name}\n"
        f"Eski fiyat: {old_price} TL\n"
        f"Yeni fiyat: {new_price} TL\n\n"
        + (f"Ürünü incelemek için: {product_url}\n\n" if product_url else "")
        + f"{BRAND}"
    )

    button = ""
    if product_url:
        button = (
            f'<p style="margin:22px 0 0;">'
            f'<a href="{product_url}" '
            f'style="display:inline-block;background:{BRAND_COLOR};color:#ffffff;'
            f'font-size:15px;font-weight:bold;text-decoration:none;padding:12px 22px;'
            f'border-radius:10px;">Ürünü incele</a></p>'
        )

    inner = (
        f'<p style="margin:0 0 18px;">'
        f'<span style="display:inline-block;font-size:14px;font-weight:bold;'
        f'color:{badge_color};background:{badge_bg};border:1px solid {badge_border};'
        f'border-radius:999px;padding:6px 14px;">{badge_text}</span></p>'
        + _info_table(
            [
                ("Ürün", product.name),
                ("Eski fiyat", f"{old_price} TL"),
                ("Yeni fiyat", f"{new_price} TL"),
            ]
        )
        + button
    )
    html_body = _html_shell(headline, intro, inner)
    _send_async(subject, text_body, html_body, [email])


# Durum koduna göre müşteriye gösterilecek kısa açıklama
_STATUS_MESSAGES = {
    "preparing": "Siparişiniz hazırlanıyor.",
    "shipped": "Siparişiniz kargoya verildi. Yakında elinizde olacak!",
    "delivered": "Siparişiniz teslim edildi. Bizi tercih ettiğiniz için teşekkürler!",
    "cancelled": "Siparişiniz iptal edildi.",
}


def send_status_update(order):
    """Sipariş durumu değiştiğinde müşteriye bilgilendirme maili."""
    if not order.email:
        return
    note = _STATUS_MESSAGES.get(order.status)
    if not note:
        # Bu durum için müşteriye mail göndermiyoruz (ör. 'Yeni' veya kullanıcı iptali).
        return
    first_name = (order.full_name or "").split(" ")[0] if order.full_name else ""
    greeting = f"Merhaba {first_name}," if first_name else "Merhaba,"
    subject = f"Sipariş durumu güncellendi — {order.order_number}"

    text_body = (
        f"{greeting}\n\n"
        f"{note}\n\n"
        f"Sipariş No: {order.order_number}\n"
        f"Güncel durum: {order.get_status_display()}\n\n"
        f"Detaylar için hesabınızdaki 'Tüm siparişlerim' bölümünü ziyaret edebilirsiniz.\n\n"
        f"{BRAND}"
    )

    inner = (
        _info_table(
            [
                ("Sipariş No", order.order_number),
                ("Güncel durum", order.get_status_display()),
            ]
        )
        + f'<p style="margin:18px 0 0;font-size:14px;font-weight:bold;color:#1e293b;line-height:1.6;">'
        f"Detaylar için hesabınızdaki <strong>“Tüm siparişlerim”</strong> bölümünü "
        f"ziyaret edebilirsiniz.</p>"
    )
    html_body = _html_shell(
        "Sipariş durumu güncellendi",
        note,
        inner,
    )
    _send_async(subject, text_body, html_body, [order.email])
