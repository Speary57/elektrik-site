from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "full_name",
        "user",
        "total",
        "status",
        "payment_status",
        "created_at",
    )
    list_filter = ("status", "payment_status", "created_at")
    search_fields = ("order_number", "full_name", "email", "phone", "user__username")
    date_hierarchy = "created_at"
    list_editable = ("status",)
    inlines = [OrderItemInline]
    readonly_fields = (
        "order_number",
        "user",
        "full_name",
        "email",
        "phone",
        "city",
        "district",
        "address",
        "note",
        "subtotal",
        "total",
        "payment_status",
        "card_last4",
        "created_at",
    )
    fieldsets = (
        (None, {"fields": ("order_number", "status", "created_at")}),
        ("Müşteri", {"fields": ("user", "full_name", "email", "phone")}),
        ("Teslimat", {"fields": ("city", "district", "address", "note")}),
        (
            "Tutarlar ve ödeme",
            {"fields": ("subtotal", "total", "payment_status", "card_last4")},
        ),
    )
