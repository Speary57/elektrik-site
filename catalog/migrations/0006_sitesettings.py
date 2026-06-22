from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_contactmessage_ip_help_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(default='Kılağuz Elektrik ve Yapı Market', max_length=160, verbose_name='Firma adı')),
                ('phone_primary', models.CharField(blank=True, default='0 (264) 432 81 92', max_length=40, verbose_name='Telefon 1')),
                ('phone_secondary', models.CharField(blank=True, default='0552 719 38 41', max_length=40, verbose_name='Telefon 2 (isteğe bağlı)')),
                ('email', models.EmailField(blank=True, default='info@kilaguzelektrik.com', max_length=254, verbose_name='E-posta')),
                ('address', models.TextField(blank=True, default='Merkez: Örnek Mahalle, Ticaret Sokak No: 12\n54100 Adapazarı / Sakarya', help_text='Her satır sitede ayrı satır olarak gösterilir.', verbose_name='Adres')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Son güncelleme')),
            ],
            options={
                'verbose_name': 'Site ayarı',
                'verbose_name_plural': 'Site ayarları',
            },
        ),
    ]
