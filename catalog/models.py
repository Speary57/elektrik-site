import re

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("Kategori adı", max_length=120)
    slug = models.SlugField(
        "URL adresi", max_length=130, unique=True, blank=True, allow_unicode=True
    )

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_list") + f"?kategori={self.slug}"


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name="Kategori",
        related_name="products",
        on_delete=models.PROTECT,
    )
    name = models.CharField("Ürün adı", max_length=200)
    slug = models.SlugField(
        "URL adresi", max_length=220, unique=True, blank=True, allow_unicode=True
    )
    description = models.TextField("Açıklama", blank=True)
    price = models.DecimalField("Fiyat (TL)", max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(
        "Güncel stok (adet)",
        default=0,
        help_text="Sitede gösterilir; sepette bu adedin üzerine çıkılamaz.",
    )
    image = models.FileField(
        "Özel fotoğraf yükle",
        upload_to="urunler/%Y/%m/",
        blank=True,
        help_text="İsteğe bağlı. Yüklerseniz galeri seçiminin üzerine yazar.",
    )
    gallery_image = models.CharField(
        "Katalog fotoğrafı",
        max_length=200,
        blank=True,
        help_text="static/img/urun-katalog/ altındaki hazır görsellerden seçin.",
    )
    is_active = models.BooleanField("Satışta", default=True)
    created_at = models.DateTimeField("Oluşturulma", auto_now_add=True)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True)
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    @property
    def max_order_quantity(self) -> int:
        """Sepet / tek eklemede izin verilen üst sınır (stok ve 99)."""
        return min(99, int(self.stock_quantity))

    @property
    def in_stock(self) -> bool:
        return int(self.stock_quantity) > 0

    @property
    def has_display_image(self) -> bool:
        return bool(self.image) or bool(self.gallery_image)

    @property
    def display_image_url(self) -> str:
        if self.image:
            return self.image.url
        if self.gallery_image:
            from django.templatetags.static import static

            return static(self.gallery_image)
        return ""


class StockNotification(models.Model):
    """'Stok gelince haber ver' talepleri.

    Ürün yeniden stoğa girdiğinde bekleyen (notified=False) kayıtlara e-posta
    gönderilir ve kayıt 'bildirildi' olarak işaretlenir.
    """

    product = models.ForeignKey(
        Product,
        verbose_name="Ürün",
        related_name="stock_notifications",
        on_delete=models.CASCADE,
    )
    email = models.EmailField("E-posta", max_length=254)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Kullanıcı",
        related_name="stock_notifications",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    notified = models.BooleanField("Bildirildi", default=False)
    created_at = models.DateTimeField("Talep tarihi", auto_now_add=True)
    notified_at = models.DateTimeField("Bildirim tarihi", null=True, blank=True)

    class Meta:
        verbose_name = "Stok bildirimi talebi"
        verbose_name_plural = "Stok bildirimi talepleri"
        ordering = ["-created_at"]
        # Aynı ürün için aynı e-posta yalnızca bir bekleyen kayıt tutsun.
        constraints = [
            models.UniqueConstraint(
                fields=["product", "email"],
                name="uniq_stock_notification_product_email",
            )
        ]

    def __str__(self):
        return f"{self.email} → {self.product} ({'bildirildi' if self.notified else 'bekliyor'})"


class ContactMessage(models.Model):
    """İletişim formundan gelen talepler (site üzerinden)."""

    ad_soyad = models.CharField("Ad soyad", max_length=160)
    email = models.EmailField("E-posta", max_length=254)
    telefon = models.CharField("Telefon", max_length=32)
    mesaj = models.TextField("Mesaj")
    aydinlatma_onay = models.BooleanField("Aydınlatma metni onayı", default=False)
    ip_address = models.CharField(
        "IP adresi",
        max_length=45,
        blank=True,
        help_text="İsteğin geldiği adres (varsa).",
    )
    created_at = models.DateTimeField("Gönderim zamanı", auto_now_add=True)

    class Meta:
        verbose_name = "İletişim mesajı"
        verbose_name_plural = "İletişim mesajları"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ad_soyad} — {self.email} ({self.created_at:%Y-%m-%d %H:%M})"


class SiteSettings(models.Model):
    """Sitedeki iletişim bilgileri vb. — admin panelinden düzenlenir (tekil kayıt)."""

    company_name = models.CharField(
        "Firma adı",
        max_length=160,
        default="Kılağuz Elektrik ve Yapı Market",
    )
    phone_primary = models.CharField(
        "Telefon 1",
        max_length=40,
        blank=True,
        default="0 (264) 432 81 92",
    )
    phone_secondary = models.CharField(
        "Telefon 2 (isteğe bağlı)",
        max_length=40,
        blank=True,
        default="0552 719 38 41",
    )
    email = models.EmailField(
        "E-posta",
        max_length=254,
        blank=True,
        default="info@kilaguzelektrik.com",
    )
    address = models.TextField(
        "Adres",
        blank=True,
        default="Merkez: Örnek Mahalle, Ticaret Sokak No: 12\n54100 Adapazarı / Sakarya",
        help_text="Her satır sitede ayrı satır olarak gösterilir.",
    )
    map_embed = models.TextField(
        "Harita (iframe kodu)",
        blank=True,
        default=(
            '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2907.646478311012'
            "!2d36.23638!3d41.0355011!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2"
            "!1s0x4087ea59164b92bd%3A0xd680356c3a335883!2zQXRhdMO8cmssIE1laG1ldCDDh2V0aW4gQ2QuIE5v"
            'OjI5LCA1NTg2MCBBc2FyY8Sxay9TYW1zdW4!5e1!3m2!1str!2str!4v1780848443577!5m2!1str!2str" '
            'width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" '
            'referrerpolicy="no-referrer-when-downgrade"></iframe>'
        ),
        help_text=(
            "Google Haritalar'dan aldığınız <iframe ...> kodunu yapıştırın. "
            "Boş bırakılırsa harita gösterilmez."
        ),
    )
    updated_at = models.DateTimeField("Son güncelleme", auto_now=True)

    class Meta:
        verbose_name = "Site ayarı"
        verbose_name_plural = "Site ayarları"

    def __str__(self):
        return "Site ayarları"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @staticmethod
    def _tel_href(value):
        digits = re.sub(r"\D+", "", value or "")
        if not digits:
            return ""
        if digits.startswith("0"):
            digits = "90" + digits[1:]
        return "+" + digits

    @property
    def phone_primary_tel(self):
        return self._tel_href(self.phone_primary)

    @property
    def phone_secondary_tel(self):
        return self._tel_href(self.phone_secondary)

    @staticmethod
    def _wa_number(value):
        digits = re.sub(r"\D+", "", value or "")
        if not digits:
            return ""
        if digits.startswith("0"):
            digits = "90" + digits[1:]
        return digits

    @property
    def phone_primary_wa(self):
        return self._wa_number(self.phone_primary)

    @property
    def phone_secondary_wa(self):
        return self._wa_number(self.phone_secondary)
