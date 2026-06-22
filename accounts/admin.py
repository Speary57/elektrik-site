from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import Address, Profile, SavedCard

User = get_user_model()


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "district", "phone", "created_at")
    list_filter = ("city",)
    search_fields = ("full_name", "phone", "city", "district", "user__username", "user__email")
    readonly_fields = ("created_at",)


@admin.register(SavedCard)
class SavedCardAdmin(admin.ModelAdmin):
    list_display = ("card_name", "user", "masked", "card_expiry", "created_at")
    search_fields = ("card_name", "user__username", "user__email")
    readonly_fields = ("created_at",)

    @admin.display(description="Kart")
    def masked(self, obj):
        return obj.masked


class UserProfileChangeForm(UserChangeForm):
    phone = forms.CharField(label="Telefon", max_length=32, required=False)
    birth_date = forms.DateField(
        label="Doğum tarihi",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        input_formats=["%Y-%m-%d", "%d.%m.%Y"],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.profile
            except Profile.DoesNotExist:
                profile = None
            if profile is not None:
                self.fields["phone"].initial = profile.phone
                self.fields["birth_date"].initial = profile.birth_date


class UserAdmin(BaseUserAdmin):
    form = UserProfileChangeForm
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_phone",
        "is_staff",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "phone", "birth_date")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    @admin.display(description="Telefon")
    def get_phone(self, obj):
        try:
            return obj.profile.phone or "—"
        except Profile.DoesNotExist:
            return "—"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        profile, _created = Profile.objects.get_or_create(user=obj)
        if "phone" in form.cleaned_data:
            profile.phone = form.cleaned_data.get("phone", "") or ""
        if "birth_date" in form.cleaned_data:
            profile.birth_date = form.cleaned_data.get("birth_date")
        profile.save()


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
