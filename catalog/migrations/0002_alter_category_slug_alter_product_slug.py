from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(
                allow_unicode=True,
                blank=True,
                max_length=130,
                unique=True,
                verbose_name="URL adresi",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(
                allow_unicode=True,
                blank=True,
                max_length=220,
                unique=True,
                verbose_name="URL adresi",
            ),
        ),
    ]
