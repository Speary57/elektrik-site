from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_alter_category_slug_alter_product_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="stock_quantity",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Sitede gösterilir; sepette bu adedin üzerine çıkılamaz.",
                verbose_name="Güncel stok (adet)",
            ),
        ),
    ]
