"""
Unit tests for Quran API client, text normalization, length filtering, and Verse of the Day generation.
"""

import pytest
from app.content.quran_api import (
    normalize_quranic_text,
    is_short_and_meaningful,
    fetch_verse,
    save_verse_to_db,
    SURAHS,
)
from app.models import ContentCategory, SourceType, VerificationStatus
from app.graphics.renderer import renderer
from app.content.captions import generate_bilingual_caption, format_source_citation


def test_normalize_quranic_text():
    """Verifies that authentic raw Uthmani orthography marks and Waqf signs are preserved."""
    raw = "فَإِنَّ مَعَ ٱلۡعُسۡرِ یُسۡرًاۖ"
    normalized = normalize_quranic_text(raw)

    # Authentic Quranic Sukoon (\u06E1) must be preserved for Uthmanic font
    assert "\u06E1" in normalized
    # Authentic Waqf mark (\u06D6 صلى) must be preserved
    assert "\u06D6" in normalized
    # Farsi Yeh (\u06CC) must become Arabic Yeh (\u064A)
    assert "\u06CC" not in normalized
    assert "يُسۡرًاۖ" in normalized


def test_fetch_verse_range():
    """Verifies fetching a paired verse range (e.g. 94:5-6) joined by authentic Ayah sign."""
    data = fetch_verse(94, (5, 6))
    assert data["chapter"] == 94
    assert data["reference"] == "94:5-6"
    assert " ۝ " in data["arabic_text"]
    assert "Ash-Sharh" in data["source_citation"]


def test_surah_dictionary_coverage():
    """Verifies that all 114 Surahs are indexed with English and Arabic names."""
    assert len(SURAHS) == 114
    assert SURAHS[1]["name_en"] == "Al-Fatihah"
    assert SURAHS[94]["name_en"] == "Ash-Sharh"
    assert SURAHS[114]["name_en"] == "An-Nas"


def test_is_short_and_meaningful_filter():
    """Verifies that small verses pass and overly verbose verses are filtered out."""
    short_verse = {
        "word_count": 4,
        "char_count": 30,
    }
    long_verse = {
        "word_count": 128,
        "char_count": 750,
    }

    assert is_short_and_meaningful(short_verse) is True
    assert is_short_and_meaningful(long_verse) is False


def test_fetch_verse_data():
    """Verifies online retrieval of an authentic verse from Quran API."""
    data = fetch_verse(94, 5)
    assert data["chapter"] == 94
    assert data["verse"] == 5
    assert data["surah_name_en"] == "Ash-Sharh"
    assert "عُسۡرِ" in data["arabic_text"] or "عُسْرِ" in data["arabic_text"]
    assert "hardship" in data["english_meaning"].lower()


def test_save_verse_to_db(db_session):
    """Verifies saving a verse creates verified ContentItem and SourceRecord."""
    verse_data = {
        "chapter": 93,
        "verse": 5,
        "surah_name_en": "Ad-Duha",
        "surah_name_ar": "الضحى",
        "arabic_text": "وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَى",
        "english_meaning": "And your Lord is going to give you, and you will be satisfied.",
        "char_count": 35,
        "word_count": 5,
    }

    item = save_verse_to_db(db_session, verse_data, auto_approve=True)
    assert item.id is not None
    assert item.category == ContentCategory.VERSE_OF_THE_DAY
    assert item.verification_status == VerificationStatus.VERIFIED
    assert item.source.source_type == SourceType.QURAN
    assert item.source.reference == "93:5"


def test_verse_rendering_and_captions(db_session, tmp_path):
    """Verifies graphic rendering and caption generation for Verse of the Day."""
    renderer.output_dir = tmp_path
    verse_data = {
        "chapter": 94,
        "verse": 5,
        "surah_name_en": "Ash-Sharh",
        "surah_name_ar": "الشرح",
        "arabic_text": "فَإِنَّ مَعَ ٱلْعُسْرِ يُسْرًا",
        "english_meaning": "For indeed, with hardship [will be] ease.",
        "char_count": 30,
        "word_count": 4,
    }
    item = save_verse_to_db(db_session, verse_data, auto_approve=True)

    # Render graphic
    feed_path, checksum, w, h = renderer.render(item, template_name="verse_of_the_day")
    assert w == 1080
    assert h == 1350
    assert len(checksum) == 64

    # Generate caption
    caption = generate_bilingual_caption(item)
    assert "آيَةُ اليَوْمِ" in caption or "Verse of the Day" in caption
    assert "#VerseOfTheDay" in caption
    assert "Surah Ash-Sharh" in caption
