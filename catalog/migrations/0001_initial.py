# Generated manually for Kılağuz project

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Kategori adı")),
                ("slug", models.SlugField(blank=True, max_length=130, unique=True, verbose_name="URL adresi")),
            ],
            options={
                "verbose_name": "Kategori",
                "verbose_name_plural": "Kategoriler",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Ürün adı")),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True, verbose_name="URL adresi")),
                ("description", models.TextField(blank=True, verbose_name="Açıklama")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Fiyat (TL)")),
                ("image", models.FileField(blank=True, upload_to="urunler/%Y/%m/", verbose_name="Fotoğraf")),
                ("is_active", models.BooleanField(default=True, verbose_name="Satışta")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.category",
                        verbose_name="Kategori",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ürün",
                "verbose_name_plural": "Ürünler",
                "ordering": ["category", "name"],
            },
        ),
    ]
