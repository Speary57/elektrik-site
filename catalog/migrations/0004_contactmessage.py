# Generated manually for ContactMessage

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_product_stock_quantity"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "ad_soyad",
                    models.CharField(max_length=160, verbose_name="Ad soyad"),
                ),
                (
                    "email",
                    models.EmailField(max_length=254, verbose_name="E-posta"),
                ),
                (
                    "telefon",
                    models.CharField(max_length=32, verbose_name="Telefon"),
                ),
                ("mesaj", models.TextField(verbose_name="Mesaj")),
                (
                    "aydinlatma_onay",
                    models.BooleanField(
                        default=False,
                        verbose_name="Aydınlatma metni onayı",
                    ),
                ),
                (
                    "ip_address",
                    models.CharField(
                        blank=True,
                        max_length=45,
                        verbose_name="IP adresi",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Gönderim zamanı",
                    ),
                ),
            ],
            options={
                "verbose_name": "İletişim mesajı",
                "verbose_name_plural": "İletişim mesajları",
                "ordering": ["-created_at"],
            },
        ),
    ]
