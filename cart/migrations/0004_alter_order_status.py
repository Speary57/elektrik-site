from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_order_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Yeni'),
                    ('preparing', 'Hazırlanıyor'),
                    ('shipped', 'Kargoda'),
                    ('delivered', 'Teslim edildi'),
                    ('cancelled', 'İptal'),
                    ('cancelled_by_user', 'Kullanıcı tarafından iptal edildi'),
                ],
                default='new',
                max_length=20,
                verbose_name='Durum',
            ),
        ),
    ]
