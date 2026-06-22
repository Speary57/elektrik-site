import io
import struct
import zlib
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Category, Product

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


def _solid_png_bytes(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """Pillow olmadan küçük düz renk PNG (RGB8)."""
    r, g, b = rgb
    row = bytes([0]) + bytes([r, g, b]) * width
    raw = row * height
    compressed = zlib.compress(raw, level=6)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def _load_fonts():
    paths = (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in paths:
        try:
            return ImageFont.truetype(path, 26), ImageFont.truetype(path, 18)
        except OSError:
            continue
    f = ImageFont.load_default()
    return f, f


def _make_placeholder_png(text: str, rgb_bg, rgb_accent, size=(640, 480)):
    if Image is not None:
        img = Image.new("RGB", size, rgb_bg)
        draw = ImageDraw.Draw(img)
        w, h = size
        draw.rounded_rectangle((24, 24, w - 24, h - 24), radius=28, outline=rgb_accent, width=4)
        font, font_small = _load_fonts()
        lines = text.split("\n")
        y = h // 2 - 36
        for i, line in enumerate(lines[:3]):
            f = font if i == 0 else font_small
            bbox = draw.textbbox((0, 0), line, font=f)
            tw = bbox[2] - bbox[0]
            draw.text(((w - tw) / 2, y), line, fill=rgb_accent, font=f)
            y += (bbox[3] - bbox[1]) + 10
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return ContentFile(buf.read(), name="urun.png")
    w, h = 480, 360
    data = _solid_png_bytes(w, h, rgb_bg)
    return ContentFile(data, name="urun.png")


class Command(BaseCommand):
    help = "Örnek kategoriler, ürünler ve görseller oluşturur."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Mevcut ürün ve kategorileri silip yeniden oluşturur.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Mevcut katalog temizlendi."))

        if Product.objects.exists():
            self.stdout.write("Ürünler zaten var. Yeniden yüklemek için --reset kullanın.")
            return

        cat_e, _ = Category.objects.get_or_create(
            slug="elektrik-malzemeleri",
            defaults={"name": "Elektrik Malzemeleri"},
        )
        cat_y, _ = Category.objects.get_or_create(
            slug="yapi-market",
            defaults={"name": "Yapı Market"},
        )

        items = [
            (
                cat_e,
                "NYM 3x2,5 mm² Yeraltı Kablosu (25 m)",
                "Bina içi tesisat ve dağıtım için uygun, HFFR dış kılıflı kablo.",
                Decimal("1890.00"),
                ((232, 240, 252), (47, 111, 191)),
                "NYM 3x2,5\n25 metre",
                8,
            ),
            (
                cat_e,
                "Topraklı Çift Priz 16 A",
                "Beyaz seri, çocuk korumalı topraklı çift priz.",
                Decimal("245.50"),
                ((240, 248, 244), (13, 148, 136)),
                "Çift Priz\n16 A",
                120,
            ),
            (
                cat_e,
                "LED Ampul 9 W E27 (2'li Paket)",
                "Sıcak beyaz 3000 K, uzun ömürlü LED ampul seti.",
                Decimal("129.90"),
                ((255, 251, 235), (196, 120, 40)),
                "LED 9W\n2'li paket",
                200,
            ),
            (
                cat_y,
                "İç Cephe Mat Beyaz Boya 15 L",
                "Kolay sürülür, düşük kokulu iç cephe boyası.",
                Decimal("1650.00"),
                ((248, 246, 242), (120, 90, 70)),
                "İç cephe\n15 L",
                18,
            ),
            (
                cat_y,
                "Metal Matkap Ucu Seti 25 mm (5 parça)",
                "Ahşap ve metal için çeşitli çaplarda matkap ucu seti.",
                Decimal("189.00"),
                ((241, 245, 249), (71, 85, 105)),
                "Matkap ucu\n5 parça",
                50,
            ),
        ]

        for category, name, desc, price, colors, img_text, stock in items:
            slug = slugify(name, allow_unicode=True)
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
            self.stdout.write(f"Eklendi: {name}")

        self.stdout.write(self.style.SUCCESS("Örnek ürünler hazır."))
        if Image is None:
            self.stdout.write(
                "Not: Pillow yok; ürün görselleri düz renk önizleme PNG olarak eklendi. "
                "Daha zengin görseller için: pip install Pillow"
            )
