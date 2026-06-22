import datetime
import threading

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.password_validation import validate_password

from .models import Profile

User = get_user_model()


class AsyncPasswordResetForm(PasswordResetForm):
    """Parola sıfırlama e-postasını arka planda gönderir.

    Böylece 'Sıfırlama bağlantısı gönder' tıklanınca onay sayfası SMTP'yi
    beklemeden anında açılır; e-posta birkaç saniye içinde ulaşır.
    """

    def send_mail(self, *args, **kwargs):
        thread = threading.Thread(
            target=super().send_mail, args=args, kwargs=kwargs, daemon=True
        )
        thread.start()


class StyledSetPasswordForm(SetPasswordForm):
    """Yeni parola alanlarına site giriş kutularıyla aynı görünümü verir."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "auth-control",
                "autocomplete": "new-password",
                "placeholder": "Yeni parolanız",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "auth-control",
                "autocomplete": "new-password",
                "placeholder": "Yeni parolanız (tekrar)",
            }
        )


class RegisterForm(forms.Form):
    full_name = forms.CharField(
        label="Ad soyad",
        max_length=150,
        min_length=3,
        widget=forms.TextInput(
            attrs={
                "class": "auth-control",
                "autocomplete": "name",
                "placeholder": "Adınız ve soyadınız",
            }
        ),
        error_messages={
            "required": "Ad soyad girin.",
            "min_length": "Ad ve soyadınızı eksiksiz yazın.",
        },
    )
    email = forms.EmailField(
        label="E-posta",
        max_length=150,
        widget=forms.EmailInput(
            attrs={
                "class": "auth-control",
                "autocomplete": "email",
                "placeholder": "ornek@eposta.com",
            }
        ),
        error_messages={
            "required": "E-posta adresinizi girin.",
            "invalid": "Geçerli bir e-posta adresi girin.",
        },
    )
    phone = forms.CharField(
        label="Telefon",
        max_length=32,
        min_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "auth-control",
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "05xx xxx xx xx",
                "maxlength": "14",
            }
        ),
        error_messages={
            "required": "Telefon numaranızı girin.",
            "min_length": "Telefon numarası çok kısa görünüyor.",
        },
    )
    password1 = forms.CharField(
        label="Parola",
        widget=forms.PasswordInput(
            attrs={
                "class": "auth-control",
                "autocomplete": "new-password",
                "placeholder": "En az 8 karakter",
            }
        ),
        error_messages={"required": "Bir parola belirleyin."},
    )
    password2 = forms.CharField(
        label="Parola (tekrar)",
        widget=forms.PasswordInput(
            attrs={
                "class": "auth-control",
                "autocomplete": "new-password",
                "placeholder": "Parolayı tekrar girin",
            }
        ),
        error_messages={"required": "Parolayı tekrar girin."},
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError("Bu e-posta ile zaten bir hesap bulunuyor.")
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Parolalar birbiriyle eşleşmiyor.")
        return p2

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        if p1:
            try:
                validate_password(p1)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        email = self.cleaned_data["email"]
        full_name = self.cleaned_data["full_name"].strip()
        parts = full_name.split()
        user = User(username=email, email=email)
        if len(parts) > 1:
            user.first_name = " ".join(parts[:-1])
            user.last_name = parts[-1]
        else:
            user.first_name = parts[0] if parts else ""
            user.last_name = ""
        user.set_password(self.cleaned_data["password1"])
        user.save()
        Profile.objects.create(user=user, phone=self.cleaned_data.get("phone", ""))
        return user


class AccountInfoForm(forms.Form):
    first_name = forms.CharField(
        label="Ad",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "auth-control", "autocomplete": "given-name"}),
        error_messages={"required": "Adınızı girin."},
    )
    last_name = forms.CharField(
        label="Soyad",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "auth-control", "autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label="E-posta",
        max_length=150,
        widget=forms.EmailInput(attrs={"class": "auth-control", "autocomplete": "email"}),
        error_messages={
            "required": "E-posta adresinizi girin.",
            "invalid": "Geçerli bir e-posta adresi girin.",
        },
    )
    phone = forms.CharField(
        label="Telefon",
        max_length=32,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "auth-control",
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "05xx xxx xx xx",
                "maxlength": "14",
                "id": "id_phone",
            }
        ),
    )
    birth_date = forms.DateField(
        label="Doğum tarihi",
        required=False,
        widget=forms.SelectDateWidget(
            years=range(datetime.date.today().year, 1939, -1),
            empty_label=("Yıl", "Ay", "Gün"),
            attrs={"class": "auth-select"},
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.user is not None:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("Bu e-posta başka bir hesapta kullanılıyor.")
        return email

    def save(self):
        user = self.user
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data.get("last_name", "").strip()
        new_email = self.cleaned_data["email"]
        user.email = new_email
        # Kullanıcı adı = e-posta olduğundan giriş tutarlılığı için onu da güncelle.
        user.username = new_email
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.phone = self.cleaned_data.get("phone", "")
        profile.birth_date = self.cleaned_data.get("birth_date")
        profile.save()
        return user


class EmailLoginForm(AuthenticationForm):
    """Kullanıcı adı = e-posta olduğundan AuthenticationForm'u e-posta için uyarlar."""

    error_messages = {
        "invalid_login": "E-posta veya parola hatalı.",
        "inactive": "Bu hesap pasif durumda.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "E-posta"
        self.fields["username"].widget = forms.EmailInput(
            attrs={
                "class": "auth-control",
                "autocomplete": "email",
                "placeholder": "ornek@eposta.com",
                "autofocus": True,
            }
        )
        self.fields["password"].label = "Parola"
        self.fields["password"].widget = forms.PasswordInput(
            attrs={
                "class": "auth-control",
                "autocomplete": "current-password",
                "placeholder": "Parolanız",
            }
        )

    def clean_username(self):
        # Girilen e-postadan gerçek kullanıcı adını bul (büyük/küçük harf duyarsız).
        # Kayıt olan kullanıcılarda kullanıcı adı = e-posta; yönetici hesaplarında
        # kullanıcı adı farklı olabilir (ör. 'aliefe'). Her iki durumu da destekler.
        value = self.cleaned_data.get("username", "").strip()
        if not value:
            return value
        match = User.objects.filter(email__iexact=value).first()
        if match is not None:
            return match.get_username()
        return value
