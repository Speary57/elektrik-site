from django import forms
from django.contrib import admin
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Category,
    ContactMessage,
    Product,
    SiteSettings,
    StockNotification,
)
from .product_images import gallery_image_choices


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["gallery_image"] = forms.ChoiceField(
            choices=gallery_image_choices(),
            required=False,
            label="Katalog fotoğrafı",
            help_text=(
                "Hazır galeriden seçin. Yeni görsel eklemek için "
                "static/img/urun-katalog/ klasörüne dosya koyup sayfayı yenileyin."
            ),
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "category", "price", "stock_quantity", "is_active", "created_at")
    list_editable = ("stock_quantity",)
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "gallery_preview")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "category",
                    "name",
                    "slug",
                    "description",
                    "price",
                    "stock_quantity",
                    "gallery_image",
                    "gallery_preview",
                    "image",
                    "is_active",
                ),
            },
        ),
        ("Sistem", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    @admin.display(description="Galeri önizleme")
    def gallery_preview(self, obj):
        if not obj or not obj.gallery_image:
            return "—"
        url = static(obj.gallery_image)
        return format_html(
            '<img src="{}" alt="" style="max-height:140px;border-radius:8px;border:1px solid #ddd;">',
            url,
        )


@admin.register(StockNotification)
class StockNotificationAdmin(admin.ModelAdmin):
    list_display = ("email", "product", "notified", "created_at", "notified_at")
    list_filter = ("notified", "created_at")
    search_fields = ("email", "product__name")
    readonly_fields = ("created_at", "notified_at")
    autocomplete_fields = ("product", "user")
    date_hierarchy = "created_at"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "ad_soyad",
        "email",
        "telefon",
        "aydinlatma_onay",
        "created_at",
        "ip_address",
    )
    list_filter = ("aydinlatma_onay", "created_at")
    search_fields = ("ad_soyad", "email", "telefon", "mesaj")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    fieldsets = (
        (None, {"fields": ("ad_soyad", "email", "telefon", "mesaj")}),
        (
            "Onay ve kayıt",
            {"fields": ("aydinlatma_onay", "ip_address", "created_at")},
        ),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    save_on_top = True
    readonly_fields = ("updated_at",)
    fieldsets = (
        ("Genel", {"fields": ("company_name",)}),
        (
            "İletişim bilgileri",
            {"fields": ("phone_primary", "phone_secondary", "email", "address")},
        ),
        ("Harita", {"fields": ("map_embed",)}),
        ("Sistem", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        # Tekil kayıt: manuel ekleme yok, kayıt otomatik oluşturulur.
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # "Site ayarları"na tıklayınca doğrudan tek kaydın düzenleme sayfasına git
        # (Kaydet butonu burada her zaman görünür).
        obj = SiteSettings.load()
        return redirect(
            reverse("admin:catalog_sitesettings_change", args=[obj.pk])
        )
