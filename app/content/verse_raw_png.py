"""
Module to fetch and manage raw Madani Mushaf verse PNGs from EveryAyah.
Mirroring the raw PNG architecture of Surah Al-Kahf.
"""

import logging
import urllib.request
from pathlib import Path
from typing import List, Tuple, Union

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

EVERYAYAH_PNG_URL_TEMPLATE = "https://everyayah.com/data/quranpngs/{chapter}_{ayah}.png"
RAW_VERSES_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "verses" / "raw"


def colorize_ayah_rgba(img: Image.Image, color_rgb: Tuple[int, int, int] = (36, 73, 54)) -> Image.Image:
    """
    Extracts black calligraphy from a grayscale/white-background image
    into smooth anti-aliased alpha, and applies brand Forest Green (#244936).
    """
    gray = ImageOps.grayscale(img.convert("RGB"))
    alpha = ImageOps.invert(gray)
    bbox = alpha.getbbox()
    if not bbox:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    solid = Image.new("RGB", img.size, color_rgb)
    colored = solid.convert("RGBA")
    colored.putalpha(alpha)
    return colored.crop(bbox)


def download_and_save_verse_raw_png(
    chapter: int,
    ayah_spec: Union[int, Tuple[int, int]],
    output_path: Path,
) -> Path:
    """
    Downloads raw Madani Mushaf ayah PNGs from EveryAyah.
    If multi-ayah, cleanly stacks them vertically.
    Saves transparent calligraphy PNG to output_path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(ayah_spec, (tuple, list)):
        ayahs = list(range(ayah_spec[0], ayah_spec[1] + 1))
    else:
        ayahs = [ayah_spec]

    ayah_images: List[Image.Image] = []
    for a in ayahs:
        url = EVERYAYAH_PNG_URL_TEMPLATE.format(chapter=chapter, ayah=a)
        req = urllib.request.Request(url, headers={"User-Agent": "DailyDhikr/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()

        from io import BytesIO
        raw_img = Image.open(BytesIO(data))
        # Trim white margins around ayah
        gray = ImageOps.grayscale(raw_img.convert("RGB"))
        alpha = ImageOps.invert(gray)
        bbox = alpha.getbbox()
        if bbox:
            cropped = raw_img.crop(bbox)
            ayah_images.append(cropped)
        else:
            ayah_images.append(raw_img)

    if not ayah_images:
        raise ValueError(f"Could not load any ayah image for {chapter}:{ayah_spec}")

    if len(ayah_images) == 1:
        ayah_images[0].save(output_path, "PNG")
        return output_path

    # Stack multi-ayah vertically with proportional gap
    gap = 25
    max_w = max(img.width for img in ayah_images)
    total_h = sum(img.height for img in ayah_images) + gap * (len(ayah_images) - 1)

    # Use white background matching original EveryAyah PNG palette
    combined = Image.new("RGB", (max_w, total_h), (255, 255, 255))
    cur_y = 0
    for img in ayah_images:
        # Center horizontally
        x = (max_w - img.width) // 2
        combined.paste(img, (x, cur_y))
        cur_y += img.height + gap

    combined.save(output_path, "PNG")
    return output_path
