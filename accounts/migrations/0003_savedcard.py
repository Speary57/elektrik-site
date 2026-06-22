import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0002_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_name', models.CharField(max_length=160, verbose_name='Kart üzerindeki isim')),
                ('card_number', models.CharField(max_length=32, verbose_name='Kart numarası')),
                ('card_expiry', models.CharField(max_length=5, verbose_name='Son kullanma (AA/YY)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Eklenme')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to=settings.AUTH_USER_MODEL, verbose_name='Kullanıcı')),
            ],
            options={
                'verbose_name': 'Kayıtlı kart',
                'verbose_name_plural': 'Kayıtlı kartlar',
                'ordering': ['-created_at'],
            },
        ),
    ]
