from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string


def generate_order_number():
    """İnsan tarafından okunabilir, benzersiz sipariş numarası (ör. KLG-7F3A9C2D)."""
    while True:
        code = "KLG-" + get_random_string(8, "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ")
        if not Order.objects.filter(order_number=code).exists():
            return code


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PREPARING = "preparing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_CANCELLED_BY_USER = "cancelled_by_user"
    STATUS_CHOICES = [
        (STATUS_NEW, "Yeni"),
        (STATUS_PREPARING, "Hazırlanıyor"),
        (STATUS_SHIPPED, "Kargoda"),
        (STATUS_DELIVERED, "Teslim edildi"),
        (STATUS_CANCELLED, "İptal"),
        (STATUS_CANCELLED_BY_USER, "Kullanıcı tarafından iptal edildi"),
    ]

    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"
    PAYMENT_CHOICES = [
        (PAYMENT_PENDING, "Bekliyor"),
        (PAYMENT_PAID, "Ödendi"),
        (PAYMENT_FAILED, "Başarısız"),
    ]

    order_number = models.CharField(
        "Sipariş numarası",
        max_length=20,
        unique=True,
        default=generate_order_number,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Kullanıcı",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    full_name = models.CharField("Ad soyad", max_length=160)
    email = models.EmailField("E-posta", max_length=254)
    phone = models.CharField("Telefon", max_length=32)
    city = models.CharField("İl", max_length=80)
    district = models.CharField("İlçe", max_length=80)
    address = models.TextField("Adres")
    note = models.CharField("Sipariş notu", max_length=400, blank=True)

    subtotal = models.DecimalField("Ara toplam", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField("Genel toplam", max_digits=12, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField("Durum", max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    payment_status = models.CharField(
        "Ödeme durumu", max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_PENDING
    )
    card_last4 = models.CharField("Kart son 4 hane", max_length=4, blank=True)

    created_at = models.DateTimeField("Oluşturulma", auto_now_add=True)

    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} — {self.full_name} ({self.total} TL)"

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def cancelled_statuses(self):
        return (self.STATUS_CANCELLED, self.STATUS_CANCELLED_BY_USER)

    @property
    def is_cancelled(self):
        return self.status in self.cancelled_statuses

    @property
    def can_cancel(self):
        """Teslim edilmemiş ve henüz iptal edilmemiş siparişler kullanıcıca iptal edilebilir."""
        return self.status in (
            self.STATUS_NEW,
            self.STATUS_PREPARING,
            self.STATUS_SHIPPED,
        )

    def restore_stock(self):
        """İptal edilen siparişteki ürünleri stoğa geri ekler."""
        from catalog.models import Product
        from django.db.models import F

        for item in self.items.all():
            if item.product_id:
                Product.objects.filter(pk=item.product_id).update(
                    stock_quantity=F("stock_quantity") + item.quantity
                )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, verbose_name="Sipariş", related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="Ürün",
        related_name="order_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product_name = models.CharField("Ürün adı", max_length=200)
    unit_price = models.DecimalField("Birim fiyat", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Adet", default=1)
    line_total = models.DecimalField("Satır toplamı", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Sipariş kalemi"
        verbose_name_plural = "Sipariş kalemleri"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"
