import re

from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Kullanıcı",
    )
    phone = models.CharField("Telefon", max_length=32, blank=True)
    birth_date = models.DateField("Doğum tarihi", null=True, blank=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profiller"

    def __str__(self):
        return f"{self.user} profili"


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name="Kullanıcı",
    )
    full_name = models.CharField("Ad soyad", max_length=160)
    phone = models.CharField("Telefon", max_length=32)
    city = models.CharField("İl", max_length=80)
    district = models.CharField("İlçe", max_length=80)
    address = models.TextField("Adres")
    created_at = models.DateTimeField("Eklenme", auto_now_add=True)

    class Meta:
        verbose_name = "Adres"
        verbose_name_plural = "Adresler"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.district}/{self.city}"

    @property
    def label(self):
        return f"{self.district} / {self.city}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Kullanıcı",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Ürün",
    )
    created_at = models.DateTimeField("Eklenme", auto_now_add=True)

    class Meta:
        verbose_name = "Favori"
        verbose_name_plural = "Favoriler"
        ordering = ["-created_at"]
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user} → {self.product}"


class SavedCard(models.Model):
    """Tanıtım amaçlı kayıtlı kart. Güvenlik gereği CVC asla saklanmaz."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cards",
        verbose_name="Kullanıcı",
    )
    card_name = models.CharField("Kart üzerindeki isim", max_length=160)
    card_number = models.CharField("Kart numarası", max_length=32)
    card_expiry = models.CharField("Son kullanma (AA/YY)", max_length=5)
    created_at = models.DateTimeField("Eklenme", auto_now_add=True)

    class Meta:
        verbose_name = "Kayıtlı kart"
        verbose_name_plural = "Kayıtlı kartlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.card_name} •••• {self.last4}"

    @property
    def digits(self):
        return re.sub(r"\D+", "", self.card_number or "")

    @property
    def last4(self):
        return self.digits[-4:]

    @property
    def masked(self):
        return f"•••• •••• •••• {self.last4}" if self.last4 else ""

