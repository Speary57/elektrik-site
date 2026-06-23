"""Galeri görsellerine karşılık gelen ürünleri kataloga ekler (idempotent)."""

from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Category, Product
from catalog.product_images import GALLERY_STATIC_SUBDIR, list_gallery_images


# (dosya_adı, kategori_slug, ürün_adı, açıklama, fiyat, stok)
GALLERY_PRODUCTS = [
    (
        "nym-3x1-5-kablo.jpg",
        "elektrik-malzemeleri",
        "NYM 3x1,5 mm² Yeraltı Kablosu (25 m)",
        "Bina içi tesisat için NYM yeraltı kablosu, 25 metre.",
        Decimal("1240.00"),
        40,
    ),
    (
        "otomatik-sigorta.jpg",
        "elektrik-malzemeleri",
        "Otomatik Sigorta 16 A C Tipi",
        "Aşırı akım ve kısa devre koruması; raya montajlı otomat.",
        Decimal("89.90"),
        120,
    ),
    (
        "kacak-akim-rolesi.jpg",
        "elektrik-malzemeleri",
        "Kaçak Akım Rölesi 2x40 A 30 mA",
        "Can güvenliği için kaçak akım koruma rölesi.",
        Decimal("540.00"),
        35,
    ),
    (
        "kombo-priz-anahtar.jpg",
        "elektrik-malzemeleri",
        "Kombo Priz Anahtar",
        "Anahtarlı priz kombinasyonu, beyaz seri.",
        Decimal("185.00"),
        80,
    ),
    (
        "led-ampul.jpg",
        "elektrik-malzemeleri",
        "LED Ampul 9 W E27",
        "Sıcak beyaz, uzun ömürlü LED ampul.",
        Decimal("79.90"),
        200,
    ),
    (
        "led-tup.jpg",
        "elektrik-malzemeleri",
        "LED Tüp 18 W",
        "Floresan yerine geçen enerji tasarruflu LED tüp.",
        Decimal("129.00"),
        90,
    ),
    (
        "tekli-anahtar-beyaz.webp",
        "elektrik-malzemeleri",
        "Tekli Anahtar Beyaz",
        "Sıva üstü tekli anahtar, beyaz seri.",
        Decimal("42.50"),
        150,
    ),
    (
        "topraklama-cubugu-klemens-seti.webp",
        "elektrik-malzemeleri",
        "Topraklama Çubuğu Klemens Seti",
        "Topraklama tesisatı için çubuk ve klemens seti.",
        Decimal("165.00"),
        60,
    ),
    (
        "wago-klemens-seti.jpg",
        "elektrik-malzemeleri",
        "Wago Klemens Seti",
        "Hızlı bağlantı için Wago tipi klemens seti.",
        Decimal("95.00"),
        100,
    ),
    (
        "kablo-kanali.jpg",
        "elektrik-malzemeleri",
        "Kablo Kanalı 25x16 mm",
        "Tesisat kabloları için PVC kablo kanalı.",
        Decimal("38.00"),
        180,
    ),
    (
        "kablo-bagi-200mm.jpg",
        "elektrik-malzemeleri",
        "Kablo Bağı 200 mm (100 adet)",
        "Naylon kablo bağı paketi, 200 mm.",
        Decimal("29.90"),
        250,
    ),
    (
        "alcipan.jpg",
        "yapi-market",
        "Alçıpan Levha 12,5 mm",
        "İç bölme ve tavan uygulamaları için alçıpan levha.",
        Decimal("185.00"),
        55,
    ),
    (
        "alcipan-vidasi.jpg",
        "yapi-market",
        "Alçıpan Vidası (100 adet)",
        "Alçıpan montajı için fosfatlı vida paketi.",
        Decimal("49.90"),
        140,
    ),
    (
        "alcipan-zimpara-sungeri.jpg",
        "yapi-market",
        "Alçıpan Zımpara Süngeri",
        "Alçıpan derz ve yüzey düzeltme için zımpara süngeri.",
        Decimal("24.90"),
        90,
    ),
    (
        "astar-boya.jpg",
        "yapi-market",
        "Astar Boya 10 L",
        "İç ve dış cephe için astar boya.",
        Decimal("890.00"),
        25,
    ),
    (
        "dis-cephe-boyasi.jpg",
        "yapi-market",
        "Dış Cephe Boyası 15 L",
        "Hava koşullarına dayanıklı dış cephe boyası.",
        Decimal("1450.00"),
        20,
    ),
    (
        "fayans-yapistiricisi.jpg",
        "yapi-market",
        "Fayans Yapıştırıcısı 25 kg",
        "Seramik ve fayans için yüksek tutuşlu yapıştırıcı.",
        Decimal("195.00"),
        45,
    ),
]


class Command(BaseCommand):
    help = "Galeri görsellerine karşılık gelen ürünleri ekler veya galeri bağlantısını günceller."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-gallery",
            action="store_true",
            help="Mevcut ürünlerde galeri görseli yoksa veya farklıysa günceller.",
        )

    def handle(self, *args, **options):
        force = options["force_gallery"]
        on_disk = {Path(rel).name: rel for rel, _ in list_gallery_images()}

        categories = {}
        added = updated = skipped = 0

        for filename, cat_slug, name, desc, price, stock in GALLERY_PRODUCTS:
            if filename not in on_disk:
                self.stdout.write(
                    self.style.WARNING(f"Görsel bulunamadı, atlandı: {filename}")
                )
                continue

            gallery_path = f"{GALLERY_STATIC_SUBDIR}/{filename}"

            if cat_slug not in categories:
                cat_name = (
                    "Elektrik Malzemeleri"
                    if cat_slug == "elektrik-malzemeleri"
                    else "Yapı Market"
                )
                categories[cat_slug], _ = Category.objects.get_or_create(
                    slug=cat_slug,
                    defaults={"name": cat_name},
                )

            slug = slugify(name, allow_unicode=True)
            product = Product.objects.filter(slug=slug).first()

            if product is None:
                Product.objects.create(
                    category=categories[cat_slug],
                    name=name,
                    slug=slug,
                    description=desc,
                    price=price,
                    stock_quantity=stock,
                    gallery_image=gallery_path,
                    is_active=True,
                )
                added += 1
                self.stdout.write(f"Eklendi: {name}")
                continue

            if force or not product.gallery_image:
                product.gallery_image = gallery_path
                product.is_active = True
                if not product.description:
                    product.description = desc
                if product.stock_quantity == 0:
                    product.stock_quantity = stock
                product.save(
                    update_fields=[
                        "gallery_image",
                        "is_active",
                        "description",
                        "stock_quantity",
                    ]
                )
                updated += 1
                self.stdout.write(f"Güncellendi: {name}")
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Tamamlandı. {added} eklendi, {updated} güncellendi, {skipped} atlandı."
            )
        )
