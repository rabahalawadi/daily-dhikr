"""
Unit tests for Surat Al-Kahf Friday Automation, Carousel Rendering, and Arabic-Only Caption.
"""

from pathlib import Path
from PIL import Image
import pytest

from app.models import ContentCategory, SourceType, ApprovalStatus, VerificationStatus
from app.content.surah_kahf import (
    START_PAGE,
    END_PAGE,
    TOTAL_PAGES,
    to_arabic_indic_digits,
    render_kahf_page,
    get_or_create_kahf_content_item,
    render_kahf_carousel_pages,
)
from app.content.captions import generate_bilingual_caption


def test_arabic_indic_digits_conversion():
    """Verifies standard numbers are correctly mapped to Arabic-Indic digits."""
    assert to_arabic_indic_digits(293) == "٢٩٣"
    assert to_arabic_indic_digits(304) == "٣٠٤"
    assert to_arabic_indic_digits(12) == "١٢"
    assert to_arabic_indic_digits(1) == "١"


def test_render_kahf_page_dimensions_and_frame(tmp_path):
    """Verifies that a rendered Mushaf page is exactly 1080x1350 and valid image."""
    # Use real page 293 from raw assets if present, else create mock mushaf image
    raw_path = Path("assets/surah_kahf/raw/page_293.png")
    if not raw_path.exists():
        raw_path = tmp_path / "mock_mushaf.png"
        mock_img = Image.new("RGBA", (1000, 1600), (240, 240, 240, 255))
        mock_img.save(raw_path)

    out_path = tmp_path / "rendered_293.png"
    rendered = render_kahf_page(293, raw_path, out_path)

    assert rendered.exists()
    assert rendered.stat().st_size > 0
    with Image.open(rendered) as img:
        assert img.size == (1080, 1350)
        assert img.format == "PNG"


def test_get_or_create_kahf_content_item(db_session):
    """Verifies that Surat Al-Kahf content item is created as approved, verified, and Arabic only."""
    item = get_or_create_kahf_content_item(db_session)

    assert item.category == ContentCategory.FRIDAY_SPECIAL
    assert item.source.source_type == SourceType.QURAN
    assert item.source.reference == "18:1-110"
    assert item.approval_status == ApprovalStatus.APPROVED
    assert item.verification_status == VerificationStatus.VERIFIED
    assert item.is_demo is False
    assert "سُورَةُ الكَهْفِ" in item.caption_ar


def test_friday_caption_is_arabic_only(db_session):
    """Verifies that generate_bilingual_caption generates purely Arabic text for FRIDAY_SPECIAL."""
    item = get_or_create_kahf_content_item(db_session)
    caption = generate_bilingual_caption(item)

    # Must contain Arabic Quran / Hadith texts
    assert "سُورَةُ الكَهْفِ" in caption
    assert "مَنْ قَرَأَ سُورَةَ الْكَهْفِ فِي يَوْمِ الْجُمُعَةِ" in caption
    assert "#سورة_الكهف" in caption

    # Must NOT contain English boilerplate headers
    assert "Meaning in English" not in caption
    assert "Verse of the Day" not in caption
    assert "Transliteration" not in caption
