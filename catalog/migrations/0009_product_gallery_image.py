from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_stocknotification"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="gallery_image",
            field=models.CharField(
                blank=True,
                help_text="static/img/urun-katalog/ altındaki hazır görsellerden seçin.",
                max_length=200,
                verbose_name="Katalog fotoğrafı",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="image",
            field=models.FileField(
                blank=True,
                help_text="İsteğe bağlı. Yüklerseniz galeri seçiminin üzerine yazar.",
                upload_to="urunler/%Y/%m/",
                verbose_name="Özel fotoğraf yükle",
            ),
        ),
    ]
