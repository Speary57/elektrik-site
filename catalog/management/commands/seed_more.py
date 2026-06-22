"""Siteye daha fazla elektrik ve yapı market ürünü ekler.

Idempotent: aynı slug'a sahip ürün varsa atlanır, böylece komut güvenle tekrar
çalıştırılabilir. Görseller mevcut seed_demo yardımcılarıyla üretilir (Pillow
varsa zengin, yoksa düz renk PNG).
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Category, Product

from .seed_demo import Image, _make_placeholder_png

# Renk paletleri (arka plan, vurgu)
E1 = ((232, 240, 252), (47, 111, 191))
E2 = ((240, 248, 244), (13, 148, 136))
E3 = ((255, 251, 235), (196, 120, 40))
E4 = ((245, 243, 255), (109, 76, 200))
Y1 = ((248, 246, 242), (120, 90, 70))
Y2 = ((241, 245, 249), (71, 85, 105))
Y3 = ((236, 253, 245), (5, 122, 85))
Y4 = ((254, 242, 242), (185, 60, 60))


class Command(BaseCommand):
    help = "Siteye daha fazla elektrik ve yapı market ürünü ekler (mevcutları korur)."

    def handle(self, *args, **options):
        cat_e, _ = Category.objects.get_or_create(
            slug="elektrik-malzemeleri",
            defaults={"name": "Elektrik Malzemeleri"},
        )
        cat_y, _ = Category.objects.get_or_create(
            slug="yapi-market",
            defaults={"name": "Yapı Market"},
        )

        items = [
            # --- Elektrik Malzemeleri ---
            (cat_e, "NYA 2,5 mm² Tek Damar Kablo (100 m)",
             "Pano ve tesisat dağıtımı için esnek tek damarlı bakır kablo.",
             Decimal("1450.00"), E1, "NYA 2,5\n100 m", 30),
            (cat_e, "Otomatik Sigorta 16 A C Tipi",
             "Aşırı akım ve kısa devre koruması; raya montajlı W otomat.",
             Decimal("89.90"), E1, "Otomat\n16 A", 150),
            (cat_e, "Kaçak Akım Rölesi 2x40 A 30 mA",
             "Can güvenliği için kaçak akım koruma rölesi (monofaze).",
             Decimal("540.00"), E2, "Kaçak akım\n40A 30mA", 40),
            (cat_e, "Anahtarlı Priz Grubu 5'li (3 m)",
             "Akım korumalı, anahtarlı 5'li uzatma priz grubu.",
             Decimal("219.90"), E2, "Priz grubu\n5'li 3 m", 90),
            (cat_e, "Sıva Altı LED Spot 7 W",
             "Gömme tavan aydınlatması için 7 W LED spot armatür.",
             Decimal("79.90"), E3, "LED Spot\n7 W", 220),
            (cat_e, "LED Projektör 50 W IP65",
             "Dış mekân için su geçirmez yüksek verimli LED projektör.",
             Decimal("459.00"), E3, "Projektör\n50 W", 60),
            (cat_e, "Buat Ek Kutusu 100x100 mm",
             "Sıva altı kablo ekleri için dayanıklı buat kutusu.",
             Decimal("24.90"), E1, "Buat\n100x100", 300),
            (cat_e, "Spiral Bükülgan Boru 16 mm (50 m)",
             "Tesisat kablolarını korumak için esnek spiral boru.",
             Decimal("320.00"), E4, "Spiral boru\n16 mm 50 m", 45),
            (cat_e, "Sıva Üstü Sigorta Panosu 12'li",
             "12 modüllü, kapaklı sıva üstü dağıtım panosu.",
             Decimal("285.00"), E4, "Pano\n12'li", 35),
            (cat_e, "Makaralı Uzatma Kablosu 3x1,5 (10 m)",
             "Termik korumalı, makaralı topraklı uzatma kablosu.",
             Decimal("399.00"), E1, "Makara\n3x1,5 10m", 55),
            (cat_e, "Hareket Sensörlü LED Tavan Armatürü 18 W",
             "Merdiven ve koridorlar için sensörlü 18 W LED armatür.",
             Decimal("289.00"), E3, "Sensörlü\n18 W", 48),
            (cat_e, "Dijital Prizli Zaman Saati",
             "Cihazları otomatik açıp kapatan programlanabilir priz.",
             Decimal("169.00"), E2, "Zaman\nsaati", 70),

            # --- Yapı Market ---
            (cat_y, "Akrilik Mastik Beyaz 310 ml",
             "Boyanabilir, çatlak ve derz dolgusu için akrilik mastik.",
             Decimal("49.90"), Y1, "Akrilik\nmastik", 260),
            (cat_y, "Şeffaf Silikon 280 ml",
             "Banyo ve mutfak için su yalıtımlı şeffaf silikon.",
             Decimal("59.90"), Y3, "Silikon\nşeffaf", 240),
            (cat_y, "Saten Alçı 25 kg",
             "Duvar yüzeyleri için ince, kolay uygulanan saten alçı.",
             Decimal("240.00"), Y1, "Saten alçı\n25 kg", 40),
            (cat_y, "Seramik Yapıştırıcı 25 kg",
             "Fayans ve seramik için yüksek tutuşlu yapıştırıcı.",
             Decimal("195.00"), Y2, "Seramik\nyapıştırıcı", 50),
            (cat_y, "Su Bazlı Ahşap Vernik 2,5 L",
             "Kokusuz, hızlı kuruyan su bazlı koruyucu vernik.",
             Decimal("320.00"), Y1, "Vernik\n2,5 L", 36),
            (cat_y, "Galvaniz Vida 4x40 mm (200 adet)",
             "Paslanmaya dayanıklı galvaniz kaplı ahşap vidası.",
             Decimal("89.90"), Y2, "Vida\n4x40", 180),
            (cat_y, "Karışık Dübel Seti (100 parça)",
             "Farklı çaplarda plastik dübel ve vida seti.",
             Decimal("69.90"), Y2, "Dübel seti\n100 parça", 160),
            (cat_y, "El Aletleri Seti 25 Parça",
             "Ev ve atölye için çantalı çok amaçlı el aleti seti.",
             Decimal("549.00"), Y4, "Alet seti\n25 parça", 28),
            (cat_y, "Çelik Başlı Çekiç 500 gr",
             "Sağlam ağaç saplı, dengeli çelik başlı çekiç.",
             Decimal("129.00"), Y2, "Çekiç\n500 gr", 95),
            (cat_y, "Su Terazisi 60 cm",
             "Yüksek görünürlüklü 3 gözlü alüminyum su terazisi.",
             Decimal("149.00"), Y3, "Su terazisi\n60 cm", 80),
            (cat_y, "Şerit Metre 5 m",
             "Otomatik kilitli, kemer klipsli 5 metre şerit metre.",
             Decimal("79.90"), Y2, "Metre\n5 m", 140),
            (cat_y, "Maskeleme Bandı 48 mm (3'lü)",
             "Boya işleri için kolay sökülen maskeleme bandı seti.",
             Decimal("59.90"), Y4, "Maskeleme\nbant 3'lü", 200),
        ]

        added = skipped = 0
        for category, name, desc, price, colors, img_text, stock in items:
            slug = slugify(name, allow_unicode=True)
            if Product.objects.filter(slug=slug).exists():
                skipped += 1
                continue
            p = Product(
                category=category,
                name=name,
                slug=slug,
                description=desc,
                price=price,
                stock_quantity=stock,
                is_active=True,
            )
            cf = _make_placeholder_png(img_text, colors[0], colors[1])
            if cf is not None:
                p.image.save(f"{slug}.png", cf, save=False)
            p.save()
            added += 1
            self.stdout.write(f"Eklendi: {name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Tamamlandı. {added} ürün eklendi, {skipped} ürün zaten vardı."
            )
        )
        if Image is None:
            self.stdout.write(
                "Not: Pillow yok; görseller düz renk önizleme PNG olarak eklendi."
            )
