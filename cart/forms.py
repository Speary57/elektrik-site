import re
from datetime import date

from django import forms

_DIGITS = re.compile(r"\D+")


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        label="Ad soyad",
        max_length=160,
        min_length=3,
        widget=forms.TextInput(
            attrs={
                "class": "checkout-control",
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
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "checkout-control",
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
                "class": "checkout-control",
                "autocomplete": "tel",
                "placeholder": "05xx xxx xx xx",
                "inputmode": "tel",
                "maxlength": "14",
            }
        ),
        error_messages={
            "required": "Telefon numaranızı girin.",
            "min_length": "Telefon numarası çok kısa görünüyor.",
        },
    )
    city = forms.CharField(
        label="İl",
        max_length=80,
        widget=forms.TextInput(
            attrs={
                "class": "checkout-control",
                "autocomplete": "address-level1",
                "placeholder": "Örn. Sakarya",
            }
        ),
        error_messages={"required": "İl girin."},
    )
    district = forms.CharField(
        label="İlçe",
        max_length=80,
        widget=forms.TextInput(
            attrs={
                "class": "checkout-control",
                "autocomplete": "address-level2",
                "placeholder": "Örn. Adapazarı",
            }
        ),
        error_messages={"required": "İlçe girin."},
    )
    address = forms.CharField(
        label="Açık adres",
        min_length=10,
        max_length=400,
        widget=forms.Textarea(
            attrs={
                "class": "checkout-control checkout-control--textarea",
                "rows": 3,
                "autocomplete": "street-address",
                "placeholder": "Mahalle, sokak, bina ve daire no…",
            }
        ),
        error_messages={
            "required": "Teslimat adresini girin.",
            "min_length": "Adresi biraz daha ayrıntılı yazın.",
        },
    )
    note = forms.CharField(
        label="Sipariş notu (isteğe bağlı)",
        required=False,
        max_length=400,
        widget=forms.Textarea(
            attrs={
                "class": "checkout-control checkout-control--textarea",
                "rows": 2,
                "placeholder": "Teslimat veya fatura ile ilgili notunuz…",
            }
        ),
    )
    save_address = forms.BooleanField(
        label="Bu adresi sonraki siparişlerim için kaydet",
        required=False,
        initial=False,
    )

    card_name = forms.CharField(
        label="Kart üzerindeki isim",
        max_length=160,
        widget=forms.TextInput(
            attrs={
                "class": "checkout-control",
                "autocomplete": "cc-name",
                "placeholder": "Kart sahibinin adı",
            }
        ),
        error_messages={"required": "Kart üzerindeki ismi girin."},
    )
    card_number = forms.CharField(
        label="Kart numarası",
        widget=forms.TextInput(
            attrs={
                "class": "checkout-control",
                "autocomplete": "cc-number",
                "inputmode": "numeric",
                "placeholder": "0000 0000 0000 0000",
                "maxlength": "23",
            }
        ),
        error_messages={"required": "Kart numarasını girin."},
    )
    card_expiry = forms.CharField(
        label="Son kullanma (AA/YY)",
        widget=forms.TextInput(
            attrs={
                "class": "checkout-control",
                "autocomplete": "cc-exp",
                "inputmode": "numeric",
                "placeholder": "AA/YY",
                "maxlength": "5",
            }
        ),
        error_messages={"required": "Son kullanma tarihini girin."},
    )
    card_cvc = forms.CharField(
        label="CVC",
        widget=forms.TextInput(
            attrs={
                "class": "checkout-control",
                "autocomplete": "cc-csc",
                "inputmode": "numeric",
                "placeholder": "123",
                "maxlength": "3",
            }
        ),
        error_messages={"required": "Kart güvenlik kodunu (CVC) girin."},
    )
    save_card = forms.BooleanField(
        label="Bu kartı sonraki siparişlerim için kaydet",
        required=False,
        initial=False,
    )

    def clean_card_number(self):
        raw = _DIGITS.sub("", self.cleaned_data.get("card_number", ""))
        if not raw.isdigit() or not (13 <= len(raw) <= 19):
            raise forms.ValidationError("Kart numarası 13-19 haneli olmalıdır.")
        return raw

    def clean_card_expiry(self):
        value = self.cleaned_data.get("card_expiry", "").strip()
        match = re.fullmatch(r"(\d{2})\s*/\s*(\d{2})", value)
        if not match:
            raise forms.ValidationError("Son kullanma tarihini AA/YY biçiminde girin.")
        month = int(match.group(1))
        if not 1 <= month <= 12:
            raise forms.ValidationError("Ay 01 ile 12 arasında olmalıdır.")
        year = 2000 + int(match.group(2))
        today = date.today()
        if (year, month) < (today.year, today.month):
            raise forms.ValidationError("Kartın son kullanma tarihi geçmiş bir tarih olamaz.")
        return f"{match.group(1)}/{match.group(2)}"

    def clean_card_cvc(self):
        value = _DIGITS.sub("", self.cleaned_data.get("card_cvc", ""))
        if not value.isdigit() or len(value) != 3:
            raise forms.ValidationError("CVC 3 haneli olmalıdır.")
        return value
