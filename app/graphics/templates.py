"""
Graphic Template specifications and color themes for Daily Dhikr.
"""

from dataclasses import dataclass
from typing import Optional
from app.config import settings


@dataclass
class TemplateConfig:
    name: str
    width: int
    height: int
    bg_color: str
    primary_text_color: str
    secondary_text_color: str
    accent_color: str
    arabic_font_size: int
    english_font_size: int
    header_title_en: str
    header_title_ar: str
    is_story: bool = False
    safe_margin_top: int = 80
    safe_margin_bottom: int = 80
    border_accent: bool = True


# Standard 1080x1350 Feed Post (Cream Background, Forest Green text, Gold Accents)
FEED_POST_TEMPLATE = TemplateConfig(
    name="feed_post",
    width=1080,
    height=1350,
    bg_color=settings.COLOR_CREAM,             # #FAF8F1
    primary_text_color=settings.COLOR_FOREST_GREEN,  # #244936
    secondary_text_color="#435E4E",
    accent_color=settings.COLOR_GOLD,          # #B99A59
    arabic_font_size=58,
    english_font_size=32,
    header_title_en="DAILY DHIKR",
    header_title_ar="ذِكْرٌ يَوْمِيّ",
    is_story=False,
    safe_margin_top=100,
    safe_margin_bottom=100,
    border_accent=True,
)

# Morning Story (Sage Green Background, Forest Green text)
MORNING_STORY_TEMPLATE = TemplateConfig(
    name="morning_story",
    width=1080,
    height=1920,
    bg_color=settings.COLOR_SAGE_GREEN,        # #E7EEE5
    primary_text_color=settings.COLOR_FOREST_GREEN,  # #244936
    secondary_text_color="#435E4E",
    accent_color=settings.COLOR_GOLD,          # #B99A59
    arabic_font_size=64,
    english_font_size=36,
    header_title_en="MORNING ADHKAR",
    header_title_ar="أَذْكَارُ الصَّبَاحِ",
    is_story=True,
    safe_margin_top=280,   # Instagram Story top UI clearance
    safe_margin_bottom=280,# Instagram Story bottom reply box clearance
    border_accent=True,
)

# Evening Story (Deep Forest Green Background, Cream text, Gold Accents)
EVENING_STORY_TEMPLATE = TemplateConfig(
    name="evening_story",
    width=1080,
    height=1920,
    bg_color=settings.COLOR_FOREST_GREEN,      # #244936
    primary_text_color=settings.COLOR_CREAM,   # #FAF8F1
    secondary_text_color=settings.COLOR_SAGE_GREEN, # #E7EEE5
    accent_color=settings.COLOR_GOLD,          # #B99A59
    arabic_font_size=64,
    english_font_size=36,
    header_title_en="EVENING ADHKAR",
    header_title_ar="أَذْكَارُ المَسَاءِ",
    is_story=True,
    safe_margin_top=280,
    safe_margin_bottom=280,
    border_accent=True,
)

# Dua Story (Cream Background, Forest Green text, Gold Accent)
DUA_STORY_TEMPLATE = TemplateConfig(
    name="dua_story",
    width=1080,
    height=1920,
    bg_color=settings.COLOR_CREAM,             # #FAF8F1
    primary_text_color=settings.COLOR_FOREST_GREEN,
    secondary_text_color="#435E4E",
    accent_color=settings.COLOR_GOLD,
    arabic_font_size=62,
    english_font_size=34,
    header_title_en="DU'A OF THE DAY",
    header_title_ar="دُعَاءُ اليَوْمِ",
    is_story=True,
    safe_margin_top=280,
    safe_margin_bottom=280,
    border_accent=True,
)

# Friday Reminder Story
FRIDAY_REMINDER_TEMPLATE = TemplateConfig(
    name="friday_reminder",
    width=1080,
    height=1920,
    bg_color=settings.COLOR_FOREST_GREEN,
    primary_text_color=settings.COLOR_CREAM,
    secondary_text_color=settings.COLOR_SAGE_GREEN,
    accent_color=settings.COLOR_GOLD,
    arabic_font_size=64,
    english_font_size=36,
    header_title_en="JUMU'AH REMINDER",
    header_title_ar="تَذْكِيرُ يَوْمِ الجُمُعَةِ",
    is_story=True,
    safe_margin_top=280,
    safe_margin_bottom=280,
    border_accent=True,
)

# Short Reminder Story
SHORT_REMINDER_TEMPLATE = TemplateConfig(
    name="short_reminder",
    width=1080,
    height=1920,
    bg_color=settings.COLOR_SAGE_GREEN,
    primary_text_color=settings.COLOR_FOREST_GREEN,
    secondary_text_color="#435E4E",
    accent_color=settings.COLOR_GOLD,
    arabic_font_size=66,
    english_font_size=36,
    header_title_en="DAILY REMINDER",
    header_title_ar="تَذْكِيرٌ يَوْمِيّ",
    is_story=True,
    safe_margin_top=280,
    safe_margin_bottom=280,
    border_accent=True,
)


# Verse of the Day Feed Post (Cream Background, Forest Green text, Gold Accent)
VERSE_OF_THE_DAY_TEMPLATE = TemplateConfig(
    name="verse_of_the_day",
    width=1080,
    height=1350,
    bg_color=settings.COLOR_CREAM,             # #FAF8F1
    primary_text_color=settings.COLOR_FOREST_GREEN,  # #244936
    secondary_text_color="#435E4E",
    accent_color=settings.COLOR_GOLD,          # #B99A59
    arabic_font_size=60,
    english_font_size=32,
    header_title_en="VERSE OF THE DAY",
    header_title_ar="آيَةُ اليَوْمِ",
    is_story=False,
    safe_margin_top=100,
    safe_margin_bottom=100,
    border_accent=True,
)

# Verse of the Day Story Post (1080x1920)
VERSE_STORY_TEMPLATE = TemplateConfig(
    name="verse_story",
    width=1080,
    height=1920,
    bg_color=settings.COLOR_SAGE_GREEN,        # #E7EEE5
    primary_text_color=settings.COLOR_FOREST_GREEN,
    secondary_text_color="#435E4E",
    accent_color=settings.COLOR_GOLD,
    arabic_font_size=64,
    english_font_size=34,
    header_title_en="VERSE OF THE DAY",
    header_title_ar="آيَةُ اليَوْمِ",
    is_story=True,
    safe_margin_top=280,
    safe_margin_bottom=280,
    border_accent=True,
)


TEMPLATES = {
    "feed_post": FEED_POST_TEMPLATE,
    "morning_story": MORNING_STORY_TEMPLATE,
    "evening_story": EVENING_STORY_TEMPLATE,
    "dua_story": DUA_STORY_TEMPLATE,
    "friday_reminder": FRIDAY_REMINDER_TEMPLATE,
    "short_reminder": SHORT_REMINDER_TEMPLATE,
    "verse_of_the_day": VERSE_OF_THE_DAY_TEMPLATE,
    "verse_story": VERSE_STORY_TEMPLATE,
}


def get_template(name: str) -> TemplateConfig:
    return TEMPLATES.get(name, FEED_POST_TEMPLATE)
