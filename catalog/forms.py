from django import forms


class ContactLeadForm(forms.Form):
    ad_soyad = forms.CharField(
        label="Adınız soyadınız",
        max_length=160,
        min_length=3,
        widget=forms.TextInput(
            attrs={
                "class": "contact-form-control",
                "autocomplete": "name",
                "placeholder": "Adınız ve soyadınız",
            }
        ),
        error_messages={
            "required": "Bu alanı doldurmanız gerekir.",
            "min_length": "Lütfen ad ve soyadınızı eksiksiz yazın.",
        },
    )
    email = forms.EmailField(
        label="E-posta adresiniz",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "contact-form-control",
                "autocomplete": "email",
                "placeholder": "ornek@eposta.com",
            }
        ),
        error_messages={
            "required": "E-posta adresinizi girin.",
            "invalid": "Geçerli bir e-posta adresi girin.",
        },
    )
    telefon = forms.CharField(
        label="Telefon numaranız",
        max_length=32,
        min_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "contact-form-control",
                "autocomplete": "tel",
                "placeholder": "05xx xxx xx xx",
                "inputmode": "tel",
            }
        ),
        error_messages={
            "required": "Telefon numaranızı girin.",
            "min_length": "Telefon numarası çok kısa görünüyor.",
        },
    )
    mesaj = forms.CharField(
        label="Mesajınız",
        min_length=10,
        max_length=4000,
        widget=forms.Textarea(
            attrs={
                "class": "contact-form-control contact-form-control--textarea",
                "rows": 5,
                "placeholder": "Talebinizi veya sorunuzu buraya yazın…",
            }
        ),
        error_messages={
            "required": "Mesajınızı yazın.",
            "min_length": "Mesajınız en az 10 karakter olmalıdır.",
        },
    )
    aydinlatma_onay = forms.BooleanField(
        label="",
        required=True,
        error_messages={
            "required": "Aydınlatma metnini okuyup kutucuğu işaretlemeniz gerekir.",
        },
        widget=forms.CheckboxInput(
            attrs={
                "class": "contact-kvkk-check",
                "required": True,
            }
        ),
    )
