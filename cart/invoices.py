"""Sipariş için PDF fatura üretimi.

`build_invoice_pdf(order)` siparişe ait profesyonel bir PDF fatura üretip
bytes olarak döndürür. reportlab kurulu değilse (veya bir hata olursa) None
döner; bu durumda e-posta fatura eki olmadan gönderilir.
"""

import logging
import os
import sys

from django.utils import timezone

logger = logging.getLogger("cart.emails")

BRAND = "Kılağuz Elektrik ve Yapı Market"
BRAND_COLOR_HEX = "#2563eb"

# Türkçe karakter desteği için aday yazı tipi dosyaları (ilk bulunan kullanılır).
_FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
]


def _register_fonts():
    """Türkçe destekli bir TTF yazı tipi kaydeder; (normal, bold) ad çiftini döndürür.

    Uygun TTF bulunamazsa reportlab'ın gömülü Helvetica'sına düşer
    (bu durumda bazı Türkçe karakterler düzgün görünmeyebilir).
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for regular, bold in _FONT_CANDIDATES:
        if os.path.exists(regular):
            try:
                pdfmetrics.registerFont(TTFont("InvoiceFont", regular))
                bold_name = "InvoiceFont-Bold"
                if os.path.exists(bold):
                    pdfmetrics.registerFont(TTFont("InvoiceFont-Bold", bold))
                else:
                    bold_name = "InvoiceFont"
                return "InvoiceFont", bold_name
            except Exception:
                continue
    return "Helvetica", "Helvetica-Bold"


def build_invoice_pdf(order):
    """Siparişe ait PDF fatura üretir; bytes döndürür veya hata/eksik kütüphanede None."""
    try:
        from io import BytesIO

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib.styles import ParagraphStyle
    except Exception as exc:
        py = sys.executable
        logger.error(
            "PDF fatura kütüphanesi yüklenemedi (%s). "
            "Django şu Python ile çalışıyor: %s\n"
            "Kurulum (sunucuyu çalıştırdığınız Python ile):\n"
            "  %s -m pip install reportlab --no-deps\n"
            "MSYS2 kullanıyorsanız ayrıca Pillow gerekir:\n"
            "  pacman -S mingw-w64-ucrt-x86_64-python-pillow",
            exc,
            py,
            py,
        )
        return None

    try:
        font, font_bold = _register_fonts()
        brand_color = colors.HexColor(BRAND_COLOR_HEX)
        muted = colors.HexColor("#64748b")
        dark = colors.HexColor("#0f172a")
        line_color = colors.HexColor("#e2e8f0")

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=f"Fatura {order.order_number}",
        )

        styles = {
            "brand": ParagraphStyle(
                "brand", fontName=font_bold, fontSize=18, textColor=brand_color,
                leading=22,
            ),
            "h1": ParagraphStyle(
                "h1", fontName=font_bold, fontSize=22, textColor=dark, leading=26,
            ),
            "label": ParagraphStyle(
                "label", fontName=font_bold, fontSize=8.5, textColor=muted,
                leading=12, spaceAfter=1,
            ),
            "value": ParagraphStyle(
                "value", fontName=font, fontSize=10.5, textColor=dark, leading=14,
            ),
            "value_b": ParagraphStyle(
                "value_b", fontName=font_bold, fontSize=10.5, textColor=dark,
                leading=14,
            ),
            "section": ParagraphStyle(
                "section", fontName=font_bold, fontSize=10, textColor=brand_color,
                leading=14, spaceBefore=6, spaceAfter=4,
            ),
            "cell": ParagraphStyle(
                "cell", fontName=font, fontSize=10, textColor=dark, leading=13,
            ),
            "cell_b": ParagraphStyle(
                "cell_b", fontName=font_bold, fontSize=10, textColor=dark,
                leading=13,
            ),
            "th": ParagraphStyle(
                "th", fontName=font_bold, fontSize=8.5, textColor=colors.white,
                leading=12,
            ),
            "footer": ParagraphStyle(
                "footer", fontName=font, fontSize=8.5, textColor=muted, leading=12,
            ),
        }

        created_local = timezone.localtime(order.created_at)
        story = []

        # Üst başlık: marka + FATURA
        header = Table(
            [[
                Paragraph(BRAND, styles["brand"]),
                Paragraph("FATURA", ParagraphStyle(
                    "ff", parent=styles["h1"], alignment=2)),
            ]],
            colWidths=[doc.width * 0.6, doc.width * 0.4],
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header)
        story.append(Spacer(1, 6))
        line = Table([[""]], colWidths=[doc.width])
        line.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 2, brand_color),
        ]))
        story.append(line)
        story.append(Spacer(1, 14))

        # Sipariş bilgileri + müşteri (iki sütun)
        info_left = [
            Paragraph("SİPARİŞ NO", styles["label"]),
            Paragraph(order.order_number, styles["value_b"]),
            Spacer(1, 6),
            Paragraph("TARİH", styles["label"]),
            Paragraph(f"{created_local:%d.%m.%Y %H:%M}", styles["value"]),
            Spacer(1, 6),
            Paragraph("DURUM", styles["label"]),
            Paragraph(order.get_status_display(), styles["value"]),
            Paragraph("ÖDEME", styles["label"]),
            Paragraph(order.get_payment_status_display(), styles["value"]),
        ]
        addr_lines = f"{order.district} / {order.city}<br/>{order.address}"
        info_right = [
            Paragraph("MÜŞTERİ", styles["label"]),
            Paragraph(order.full_name, styles["value_b"]),
            Paragraph(order.email or "", styles["value"]),
            Paragraph(order.phone or "", styles["value"]),
            Spacer(1, 6),
            Paragraph("TESLİMAT ADRESİ", styles["label"]),
            Paragraph(addr_lines, styles["value"]),
        ]
        info = Table(
            [[info_left, info_right]],
            colWidths=[doc.width * 0.5, doc.width * 0.5],
        )
        info.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("LEFTPADDING", (1, 0), (1, 0), 10),
        ]))
        story.append(info)
        story.append(Spacer(1, 18))

        # Ürün tablosu
        data = [[
            Paragraph("ÜRÜN", styles["th"]),
            Paragraph("ADET", ParagraphStyle("thc", parent=styles["th"], alignment=1)),
            Paragraph("BİRİM FİYAT", ParagraphStyle("thr", parent=styles["th"], alignment=2)),
            Paragraph("TUTAR", ParagraphStyle("thr2", parent=styles["th"], alignment=2)),
        ]]
        right = ParagraphStyle("cr", parent=styles["cell"], alignment=2)
        center = ParagraphStyle("cc", parent=styles["cell"], alignment=1)
        for it in order.items.all():
            data.append([
                Paragraph(it.product_name, styles["cell"]),
                Paragraph(str(it.quantity), center),
                Paragraph(f"{it.unit_price} TL", right),
                Paragraph(f"{it.line_total} TL", ParagraphStyle(
                    "crb", parent=styles["cell_b"], alignment=2)),
            ])

        col_widths = [doc.width * 0.46, doc.width * 0.14,
                      doc.width * 0.20, doc.width * 0.20]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), brand_color),
            ("TOPPADDING", (0, 0), (-1, 0), 7),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, line_color),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f8fafc")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))

        # Toplamlar
        totals = Table(
            [
                [Paragraph("Ara toplam", styles["value"]),
                 Paragraph(f"{order.subtotal} TL", ParagraphStyle(
                     "tr", parent=styles["value"], alignment=2))],
                [Paragraph("Genel toplam", ParagraphStyle(
                    "tg", parent=styles["value_b"], fontSize=12)),
                 Paragraph(f"{order.total} TL", ParagraphStyle(
                     "tgr", parent=styles["value_b"], fontSize=12,
                     alignment=2, textColor=brand_color))],
            ],
            colWidths=[doc.width * 0.7, doc.width * 0.3],
        )
        totals.setStyle(TableStyle([
            ("LINEABOVE", (0, 1), (-1, 1), 1, line_color),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ]))
        story.append(totals)

        if order.note:
            story.append(Spacer(1, 14))
            story.append(Paragraph("SİPARİŞ NOTU", styles["section"]))
            story.append(Paragraph(order.note, styles["value"]))

        story.append(Spacer(1, 26))
        story.append(Paragraph(
            f"Bu fatura {BRAND} tarafından otomatik olarak oluşturulmuştur. "
            f"Bizi tercih ettiğiniz için teşekkür ederiz.",
            styles["footer"],
        ))

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        logger.info("PDF fatura üretildi (%s bytes) -> %s",
                    len(pdf), order.order_number)
        return pdf
    except Exception:
        logger.exception("PDF fatura üretilirken hata oluştu.")
        return None
