import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=160, verbose_name='Ad soyad')),
                ('phone', models.CharField(max_length=32, verbose_name='Telefon')),
                ('city', models.CharField(max_length=80, verbose_name='İl')),
                ('district', models.CharField(max_length=80, verbose_name='İlçe')),
                ('address', models.TextField(verbose_name='Adres')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Eklenme')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL, verbose_name='Kullanıcı')),
            ],
            options={
                'verbose_name': 'Adres',
                'verbose_name_plural': 'Adresler',
                'ordering': ['-created_at'],
            },
        ),
    ]
