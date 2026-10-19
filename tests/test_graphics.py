"""
Tests for graphic generation, dimensions, text wrapping, and template layouts.
"""

from pathlib import Path
import pytest
from app.graphics.renderer import renderer, wrap_arabic_lines, wrap_english_lines
from app.graphics.fonts import get_arabic_font, get_english_font
from app.graphics.templates import TEMPLATES, get_template


def test_feed_post_dimensions_and_checksum(sample_approved_content, tmp_path):
    """Verifies that feed posts are rendered to 1080x1350 with a valid SHA256 checksum."""
    renderer.output_dir = tmp_path
    img_path, checksum, width, height = renderer.render(sample_approved_content, template_name="feed_post")

    assert width == 1080
    assert height == 1350
    assert len(checksum) == 64
    assert Path(img_path).exists()
    assert Path(img_path).stat().st_size > 0


def test_story_dimensions(sample_approved_content, tmp_path):
    """Verifies that Instagram Stories are rendered to 1080x1920."""
    renderer.output_dir = tmp_path
    img_path, checksum, width, height = renderer.render(sample_approved_content, template_name="morning_story")

    assert width == 1080
    assert height == 1920
    assert len(checksum) == 64
    assert Path(img_path).exists()


def test_all_templates_render_successfully(sample_approved_content, tmp_path):
    """Ensures each of the 6 branded templates renders cleanly without exceptions."""
    renderer.output_dir = tmp_path
    for name in TEMPLATES.keys():
        path, csum, w, h = renderer.render(sample_approved_content, template_name=name)
        assert Path(path).exists()
        assert len(csum) == 64


def test_text_wrapping():
    """Verifies that long text is wrapped into multiple lines."""
    font_ar = get_arabic_font(40)
    font_en = get_english_font(30)

    long_ar = "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ عَدَدَ خَلْقِهِ وَرِضَا نَفْسِهِ وَزِنَةَ عَرْشِهِ وَمِدَادَ كَلِمَاتِهِ"
    lines_ar = wrap_arabic_lines(long_ar, font_ar, max_width=500)
    assert len(lines_ar) > 1

    long_en = "Glory be to Allah and all praise is due to Him, according to the number of His creation and the pleasure of His self."
    lines_en = wrap_english_lines(long_en, font_en, max_width=400)
    assert len(lines_en) > 1
