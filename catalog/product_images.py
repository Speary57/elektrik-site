"""Static ürün galerisi — admin panelinde seçim listesi."""

from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings

GALLERY_STATIC_SUBDIR = "img/urun-katalog"
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def gallery_dir() -> Path:
    return Path(settings.BASE_DIR) / "static" / GALLERY_STATIC_SUBDIR


def _label_from_filename(filename: str) -> str:
    stem = Path(filename).stem.replace("-", " ")
    return stem.title()


def list_gallery_images() -> list[tuple[str, str]]:
    """(static_yol, görünen_ad) çiftleri — dosya adına göre sıralı."""
    base = gallery_dir()
    if not base.is_dir():
        return []

    items: list[tuple[str, str]] = []
    for name in sorted(os.listdir(base)):
        if Path(name).suffix.lower() not in _IMAGE_EXTENSIONS:
            continue
        rel = f"{GALLERY_STATIC_SUBDIR}/{name}"
        items.append((rel, _label_from_filename(name)))
    return items


def gallery_image_choices() -> list[tuple[str, str]]:
    return [("", "— Galeriden seçin —")] + list_gallery_images()
