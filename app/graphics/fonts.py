"""
Font management, Arabic text-shaping, and bidirectional layout handling.
Supports Cairo, Noto Sans Arabic, and Amiri with zero broken characters and clean Tashkeel.
"""

import logging
from pathlib import Path
from typing import Optional
from PIL import ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from app.config import settings

logger = logging.getLogger(__name__)

# Mapping from Presentation Forms-B isolated glyphs to standard Arabic base characters.
# Modern fonts (like Google's Cairo) map isolated letters directly to standard Unicode
# points (U+0621-U+064A) rather than deprecated Presentation Forms.
ISOLATED_TO_STANDARD = {
    0xFE80: 0x0621,  # Hamza
    0xFE81: 0x0622,  # Alef Madda
    0xFE83: 0x0623,  # Alef Hamza Above
    0xFE85: 0x0624,  # Waw Hamza
    0xFE87: 0x0625,  # Alef Hamza Below
    0xFE89: 0x0626,  # Yeh Hamza
    0xFE8D: 0x0627,  # Alef
    0xFE8F: 0x0628,  # Beh
    0xFE93: 0x0629,  # Teh Marbuta
    0xFE95: 0x062A,  # Teh
    0xFE99: 0x062B,  # Theh
    0xFE9D: 0x062C,  # Jeem
    0xFEA1: 0x062D,  # Hah
    0xFEA5: 0x062E,  # Khah
    0xFEA9: 0x062F,  # Dal
    0xFEAB: 0x0630,  # Thal
    0xFEAD: 0x0631,  # Reh
    0xFEAF: 0x0632,  # Zain
    0xFEB1: 0x0633,  # Seen
    0xFEB5: 0x0634,  # Sheen
    0xFEB9: 0x0635,  # Sad
    0xFEBD: 0x0636,  # Dad
    0xFEC1: 0x0637,  # Tah
    0xFEC5: 0x0638,  # Zah
    0xFEC9: 0x0639,  # Ain
    0xFECD: 0x063A,  # Ghain
    0xFED1: 0x0641,  # Feh
    0xFED5: 0x0642,  # Qaf
    0xFED9: 0x0643,  # Kaf
    0xFEDD: 0x0644,  # Lam
    0xFEE1: 0x0645,  # Meem
    0xFEE5: 0x0646,  # Noon
    0xFEE9: 0x0647,  # Heh
    0xFEED: 0x0648,  # Waw
    0xFEEF: 0x0649,  # Alef Maksura
    0xFEF1: 0x064A,  # Yeh
}

# Preconfigured reshapers
reshaper_clean = arabic_reshaper.ArabicReshaper(configuration={
    'delete_harakat': True,
    'support_ligatures': True,
    'language': 'Arabic',
})

reshaper_with_tashkeel = arabic_reshaper.ArabicReshaper(configuration={
    'delete_harakat': False,
    'support_ligatures': True,
    'language': 'Arabic',
})


def shape_arabic_text(text: str, strip_tashkeel: Optional[bool] = None) -> str:
    """
    Transforms raw Arabic text with proper ligature shaping and right-to-left bidi reordering.
    Eliminates broken characters by mapping isolated glyphs to standard Unicode, and
    eliminates overlapping/conflicting diacritics when strip_tashkeel is True.
    """
    if not text:
        return ""
    try:
        do_strip = settings.STRIP_TASHKEEL_ON_IMAGES if strip_tashkeel is None else strip_tashkeel
        r = reshaper_clean if do_strip else reshaper_with_tashkeel
        reshaped = r.reshape(text)

        # Map Presentation Forms-B isolated glyphs to standard Unicode codepoints
        # so Cairo font renders them seamlessly with zero .notdef tofu boxes.
        fixed = [chr(ISOLATED_TO_STANDARD[ord(c)]) if ord(c) in ISOLATED_TO_STANDARD else c for c in reshaped]
        bidi_text = get_display("".join(fixed))
        return bidi_text
    except Exception as e:
        logger.warning(f"Error shaping Arabic text: {e}. Falling back to original.")
        return text


def load_font(font_path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Loads a TrueType/OpenType font at the specified size with graceful fallback.
    Sets variable font axes for optimal contrast:
    - Cairo: Weight 700 (Bold)
    - Inter: Weight 550 (Medium/SemiBold)
    """
    if font_path.exists():
        try:
            font = ImageFont.truetype(str(font_path), size)
            if hasattr(font, "set_variation_by_axes"):
                path_lower = str(font_path).lower()
                if "cairo" in path_lower:
                    try:
                        font.set_variation_by_axes([700, 0])  # Weight 700 (Bold), Slant 0
                    except Exception:
                        pass
                elif "inter" in path_lower:
                    try:
                        font.set_variation_by_axes([14, 550])  # Optical size 14, Weight 550
                    except Exception:
                        pass
            return font
        except Exception as e:
            logger.warning(f"Failed to load font from {font_path}: {e}")

    # Fallbacks with complete Arabic coverage
    system_fallbacks = [
        str(settings.FONTS_DIR / "Cairo.ttf"),
        str(settings.FONTS_DIR / "NotoSansArabic.ttf"),
        str(settings.FONTS_DIR / "Amiri-Bold.ttf"),
        "Cairo.ttf",
        "NotoSansArabic-Regular.ttf",
        "trado.ttf",
        "tradbdo.ttf",
        "tahoma.ttf",
        "arial.ttf",
    ]
    for fb in system_fallbacks:
        try:
            return ImageFont.truetype(fb, size)
        except Exception:
            continue

    logger.warning(f"Falling back to Pillow default bitmap font for size {size}")
    return ImageFont.load_default()


def get_arabic_font(size: int = 56) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Returns the primary verified Arabic font (Cairo)."""
    return load_font(settings.get_arabic_font_path(), size)


def get_english_font(size: int = 36) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Returns the primary English font (Inter)."""
    return load_font(settings.get_inter_font_path(), size)
