"""
Bilingual Caption Generator for Instagram Feed Posts and Stories.
Produces respectful, beautifully structured, and verified captions in Arabic and English.
"""

from typing import Optional
from app.models import ContentItem, SourceType

MAX_INSTAGRAM_CAPTION_LENGTH = 2200

DEFAULT_HASHTAGS = [
    "#DailyDhikr",
    "#Dhikr",
    "#Remembrance",
    "#IslamicReminders",
    "#Dua",
    "#Hadith",
    "#Quran",
    "#PeaceOfHeart",
    "#ذكر_الله",
    "#اذكار",
    "#طمأنينة",
]


def format_source_citation(item: ContentItem) -> str:
    """Formats a clean, standardized citation from the attached source record."""
    if not item.source:
        return "Source: Unverified"

    src = item.source
    if src.source_type == SourceType.QURAN:
        return f"📖 {src.source_name} [{src.reference}]"
    elif src.source_type == SourceType.HADITH:
        grade_info = f" ({src.hadith_grade})" if src.hadith_grade else ""
        return f"📜 {src.source_name}, {src.reference}{grade_info}"
    else:
        return f"📚 {src.source_name} ({src.reference})"


def generate_bilingual_caption(
    item: ContentItem,
    include_transliteration: bool = True,
    include_hashtags: bool = True,
    custom_closing: Optional[str] = None
) -> str:
    """
    Constructs an Instagram caption containing:
    1. Arabic original text
    2. English translation
    3. Transliteration (if present and enabled)
    4. Verified source citation
    5. Gentle spiritual closing
    6. Curated hashtags

    Ensures result stays within Instagram's 2,200 character limit.
    """
    # If custom stored captions already exist, use them
    if item.caption_ar and item.caption_en:
        arabic_part = item.caption_ar.strip()
        english_part = item.caption_en.strip()
    else:
        arabic_part = item.arabic_text.strip()
        english_part = item.english_meaning.strip()

    citation = format_source_citation(item)

    closing = custom_closing or "May this remembrance bring peace and tranquility to your day.\nاللَّهُمَّ أَعِنَّا عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ."

    parts = [
        "﷽",
        "",
        "✦ الذِّكْرُ بِالعَرَبِيَّةِ / Arabic:",
        arabic_part,
        "",
        "✦ Meaning in English:",
        english_part,
    ]

    if include_transliteration and item.transliteration and item.transliteration.strip():
        parts.extend([
            "",
            "✦ Transliteration:",
            item.transliteration.strip(),
        ])

    parts.extend([
        "",
        "✦ Reference / المرجع:",
        citation,
        "",
        "─" * 20,
        closing,
    ])

    if include_hashtags:
        hashtags_str = " ".join(DEFAULT_HASHTAGS)
        parts.extend([
            "",
            hashtags_str
        ])

    caption = "\n".join(parts)

    # Safety truncation if somehow exceeding limit
    if len(caption) > MAX_INSTAGRAM_CAPTION_LENGTH:
        # Remove hashtags first
        if include_hashtags:
            return generate_bilingual_caption(item, include_transliteration, include_hashtags=False, custom_closing=custom_closing)
        # Otherwise trim safely
        caption = caption[:MAX_INSTAGRAM_CAPTION_LENGTH - 3] + "..."

    return caption
