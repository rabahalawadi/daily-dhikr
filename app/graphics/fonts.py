"""
Font management, Arabic text-shaping, and bidirectional layout handling.
"""

import logging
from pathlib import Path
from typing import Optional
from PIL import ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from app.config import settings

logger = logging.getLogger(__name__)

# Configure arabic reshaper for optimal Tashkeel (harakat) and ligature handling
RESHAPER_CONFIG = {
    'delete_harakat': False,
    'support_ligatures': True,
    'language': 'Arabic',
}
reshaper = arabic_reshaper.ArabicReshaper(configuration=RESHAPER_CONFIG)


def shape_arabic_text(text: str) -> str:
    """
    Transforms raw Arabic text with proper ligature shaping and right-to-left bidi reordering
    so that standard graphic renderers like Pillow draw it correctly.
    """
    if not text:
        return ""
    try:
        # Step 1: Reshape characters (connect initial, medial, final, isolated forms)
        reshaped = reshaper.reshape(text)
        # Step 2: Apply BiDi algorithm to reorder text right-to-left for visual drawing
        bidi_text = get_display(reshaped)
        return bidi_text
    except Exception as e:
        logger.warning(f"Error shaping Arabic text: {e}. Falling back to original.")
        return text


def load_font(font_path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Loads a TrueType font at the specified size with graceful fallback to default font.
    """
    if font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), size)
        except Exception as e:
            logger.warning(f"Failed to load font from {font_path}: {e}")
    
    # Try system font fallbacks
    system_fallbacks = [
        "Cairo.ttf",
        "NotoSansArabic-Regular.ttf",
        "seguiemj.ttf",
        "arial.ttf"
    ]
    for fb in system_fallbacks:
        try:
            return ImageFont.truetype(fb, size)
        except Exception:
            continue

    logger.warning(f"Falling back to Pillow default bitmap font for size {size}")
    return ImageFont.load_default()


def get_arabic_font(size: int = 56) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Returns the primary Arabic font (Cairo)."""
    return load_font(settings.get_cairo_font_path(), size)


def get_english_font(size: int = 36) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Returns the primary English font (Inter)."""
    return load_font(settings.get_inter_font_path(), size)
