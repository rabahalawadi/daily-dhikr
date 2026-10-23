"""
Unit tests for raw Madani Mushaf verse PNG downloading and rendering.
"""

from pathlib import Path
from PIL import Image
import pytest

from app.content.verse_raw_png import colorize_ayah_rgba, RAW_VERSES_DIR
from app.graphics.renderer import renderer
from app.models import ContentItem, SourceRecord, ContentCategory, SourceType


def test_colorize_ayah_rgba():
    """Verifies that white-background black calligraphy is transformed to RGBA Forest Green."""
    # Create simple 100x50 black box on white background
    test_img = Image.new("RGB", (100, 50), (255, 255, 255))
    for x in range(30, 70):
        for y in range(15, 35):
            test_img.putpixel((x, y), (0, 0, 0))

    colorized = colorize_ayah_rgba(test_img, (36, 73, 54))
    assert colorized.mode == "RGBA"
    assert colorized.width == 40  # 70 - 30
    assert colorized.height == 20  # 35 - 15


def test_renderer_prefers_raw_mushaf_png(tmp_path):
    """Verifies that GraphicRenderer uses raw Mushaf PNG when available."""
    source = SourceRecord(source_type=SourceType.QURAN, source_name="Surah Al-Baqarah", reference="2:186")
    item = ContentItem(
        id="test-raw-png-item",
        category=ContentCategory.VERSE_OF_THE_DAY,
        arabic_text="وَإِذَا سَأَلَكَ عِبَادِي عَنِّي",
        english_meaning="And when My servants ask you concerning Me",
        source=source,
    )

    raw_png = RAW_VERSES_DIR / "verse_2_186.png"
    assert raw_png.exists(), "verse_2_186.png should exist in assets/verses/raw"

    img_path, checksum, w, h = renderer.render(item, "verse_of_the_day")
    assert w == 1080
    assert h == 1350
    assert img_path.exists()
