"""
Tests for Arabic text shaping, right-to-left BiDi reordering, and unicode validation.
"""

import pytest
from app.graphics.fonts import shape_arabic_text, get_arabic_font
from app.content.verification import contains_arabic, compute_arabic_checksum


def test_arabic_regex_detection():
    """Verifies that Arabic text is properly detected and English text without Arabic is rejected."""
    assert contains_arabic("سُبْحَانَ اللَّهِ") is True
    assert contains_arabic("الحمد لله رب العالمين") is True
    assert contains_arabic("Just plain English text") is False
    assert contains_arabic("1234567890") is False


def test_arabic_shaping_preserves_content():
    """Ensures Arabic shaping produces non-empty display text."""
    raw = "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ"
    shaped = shape_arabic_text(raw)
    assert shaped != ""
    assert len(shaped) > 0


def test_arabic_checksum_consistency():
    """Verifies that normalized text produces identical checksums regardless of whitespace."""
    text1 = "سُبْحَانَ اللَّهِ   وَبِحَمْدِهِ"
    text2 = " سُبْحَانَ اللَّهِ وَبِحَمْدِهِ "
    assert compute_arabic_checksum(text1) == compute_arabic_checksum(text2)


def test_arabic_font_loading():
    """Verifies that font loader returns a valid font instance without crashing."""
    font = get_arabic_font(size=40)
    assert font is not None


def test_harfbuzz_measurement():
    """Verifies that HarfBuzz measures Arabic strings with Tashkeel accurately."""
    from app.graphics.fonts import measure_arabic_harfbuzz
    from app.config import settings

    cairo_path = settings.get_arabic_font_path()
    text = "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ"

    w40 = measure_arabic_harfbuzz(text, cairo_path, font_size=40)
    w60 = measure_arabic_harfbuzz(text, cairo_path, font_size=60)

    assert w40 > 0
    assert w60 > w40


def test_harfbuzz_rendering_with_tashkeel():
    """Verifies that HarfBuzz renders complex Arabic diacritics directly to an image."""
    from PIL import Image
    from app.graphics.fonts import render_arabic_harfbuzz
    from app.config import settings

    cairo_path = settings.get_arabic_font_path()
    image = Image.new("RGB", (800, 200), "#FAF8F1")
    text = "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ"

    w = render_arabic_harfbuzz(
        target_image=image,
        line=text,
        font_path=cairo_path,
        font_size=40,
        color_hex="#244936",
        center_x=400,
        baseline_y=100,
        weight=450.0,
    )
    assert w > 0

    # Ensure image contains colored pixels from rendered text
    raw_bytes = image.tobytes()
    # Check that not all bytes are background (#FAF8F1 -> 250, 248, 241)
    assert any(b not in (250, 248, 241) for b in raw_bytes)


def test_font_weights_cairo_and_inter():
    """Verifies Cairo Medium and Inter SemiBold/Bold are loaded with proper weights."""
    from app.graphics.fonts import get_arabic_font, get_english_font

    cairo_font = get_arabic_font(size=48, weight=450)
    inter_font = get_english_font(size=32, weight=600)

    assert cairo_font is not None
    assert inter_font is not None
