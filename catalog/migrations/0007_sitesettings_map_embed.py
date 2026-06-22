from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_sitesettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='map_embed',
            field=models.TextField(
                blank=True,
                default=(
                    '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2907.646478311012'
                    '!2d36.23638!3d41.0355011!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2'
                    '!1s0x4087ea59164b92bd%3A0xd680356c3a335883!2zQXRhdMO8cmssIE1laG1ldCDDh2V0aW4gQ2QuIE5v'
                    'OjI5LCA1NTg2MCBBc2FyY8Sxay9TYW1zdW4!5e1!3m2!1str!2str!4v1780848443577!5m2!1str!2str" '
                    'width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" '
                    'referrerpolicy="no-referrer-when-downgrade"></iframe>'
                ),
                help_text=(
                    "Google Haritalar'dan aldığınız <iframe ...> kodunu yapıştırın. "
                    "Boş bırakılırsa harita gösterilmez."
                ),
                verbose_name='Harita (iframe kodu)',
            ),
        ),
    ]
