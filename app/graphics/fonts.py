"""
Font management, Arabic text-shaping, and bidirectional layout handling.
Features high-precision HarfBuzz OpenType layout with Cairo, Noto Sans Arabic, and Amiri.
Preserves complete Tashkeel (harakat) without overlaps using GPOS anchor positioning,
and balances font weights (Cairo Medium / Inter SemiBold).
"""

import logging
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from app.config import settings

logger = logging.getLogger(__name__)

# Check for HarfBuzz and FreeType engines
try:
    import uharfbuzz as hb
    import freetype
    HAS_HARFBUZZ = True
except ImportError:
    HAS_HARFBUZZ = False
    logger.info("uharfbuzz or freetype-py not installed; falling back to standard Pillow text renderer.")

# Mapping from Presentation Forms-B isolated glyphs to standard Arabic base characters.
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
reshaper_with_tashkeel = arabic_reshaper.ArabicReshaper(configuration={
    'delete_harakat': False,
    'support_ligatures': True,
    'language': 'Arabic',
})

reshaper_clean = arabic_reshaper.ArabicReshaper(configuration={
    'delete_harakat': True,
    'support_ligatures': True,
    'language': 'Arabic',
})


def shape_arabic_text(text: str, strip_tashkeel: Optional[bool] = None) -> str:
    """
    Transforms raw Arabic text with proper ligature shaping and right-to-left bidi reordering.
    Eliminates broken characters by mapping isolated glyphs to standard Unicode.
    """
    if not text:
        return ""
    try:
        do_strip = settings.STRIP_TASHKEEL_ON_IMAGES if strip_tashkeel is None else strip_tashkeel
        r = reshaper_clean if do_strip else reshaper_with_tashkeel
        reshaped = r.reshape(text)

        # Map Presentation Forms-B isolated glyphs to standard Unicode codepoints
        fixed = [chr(ISOLATED_TO_STANDARD[ord(c)]) if ord(c) in ISOLATED_TO_STANDARD else c for c in reshaped]
        bidi_text = get_display("".join(fixed))
        return bidi_text
    except Exception as e:
        logger.warning(f"Error shaping Arabic text: {e}. Falling back to original.")
        return text


def load_font(
    font_path: Path,
    size: int,
    weight: Optional[int] = None,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Loads a TrueType/OpenType font at the specified size with graceful fallback.
    Sets variable font axes for balanced typography:
    - Cairo: Default Weight 450 (Regular/Medium - balanced, elegant, not too thick)
    - Inter: Default Weight 600 (SemiBold - solid, high contrast, not too thin)
    """
    if font_path.exists():
        try:
            font = ImageFont.truetype(str(font_path), size)
            if hasattr(font, "set_variation_by_axes"):
                path_lower = str(font_path).lower()
                if "cairo" in path_lower:
                    try:
                        w = weight if weight is not None else 450
                        font.set_variation_by_axes([w, 0])
                    except Exception:
                        pass
                elif "inter" in path_lower:
                    try:
                        w = weight if weight is not None else 600
                        font.set_variation_by_axes([14, w])
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


def get_arabic_font(size: int = 56, weight: int = 450) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Returns the primary verified Arabic font (Cairo) with balanced Medium weight."""
    return load_font(settings.get_arabic_font_path(), size, weight=weight)


def get_english_font(size: int = 36, weight: int = 600) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Returns the primary English font (Inter) with SemiBold/Bold weight."""
    return load_font(settings.get_inter_font_path(), size, weight=weight)


# -----------------------------------------------------------------------------
# HarfBuzz OpenType Shaping Engine
# -----------------------------------------------------------------------------

_font_bytes_cache: dict[str, bytes] = {}
_ft_faces_cache: dict[str, freetype.Face] = {} if HAS_HARFBUZZ else {}


def _get_font_bytes(font_path: Path) -> bytes:
    key = str(font_path)
    if key not in _font_bytes_cache:
        with open(font_path, "rb") as f:
            _font_bytes_cache[key] = f.read()
    return _font_bytes_cache[key]


def _get_ft_face(font_path: Path) -> freetype.Face:
    key = str(font_path)
    if key not in _ft_faces_cache:
        _ft_faces_cache[key] = freetype.Face(key)
    return _ft_faces_cache[key]


def measure_arabic_harfbuzz(
    text: str,
    font_path: Path,
    font_size: int,
    weight: float = 450.0,
) -> int:
    """Measures pixel width of an Arabic string using HarfBuzz OpenType layout."""
    if not HAS_HARFBUZZ or not font_path.exists():
        # Fallback to Pillow bbox
        font = get_arabic_font(font_size)
        shaped = shape_arabic_text(text)
        bbox = font.getbbox(shaped)
        return bbox[2] - bbox[0]

    font_data = _get_font_bytes(font_path)
    hb_face = hb.Face(hb.Blob(font_data))
    hb_font = hb.Font(hb_face)
    hb_font.scale = (font_size * 64, font_size * 64)
    try:
        hb_font.set_variations({"wght": weight})
    except Exception:
        pass

    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)

    total_w = sum(pos.x_advance for pos in buf.glyph_positions) // 64
    return total_w


def render_arabic_harfbuzz(
    target_image: Image.Image,
    line: str,
    font_path: Path,
    font_size: int,
    color_hex: str,
    center_x: int,
    baseline_y: int,
    weight: float = 450.0,
) -> int:
    """
    Renders an Arabic text line with full Tashkeel (harakat) using HarfBuzz GPOS positioning
    and FreeType glyph rasterization directly onto target_image.
    Returns the pixel width of the line.
    """
    if not HAS_HARFBUZZ or not font_path.exists():
        # Fallback to standard Pillow draw
        from PIL import ImageDraw
        draw = ImageDraw.Draw(target_image)
        font = get_arabic_font(font_size)
        shaped = shape_arabic_text(line)
        draw.text((center_x, baseline_y), shaped, font=font, fill=color_hex, anchor="mm")
        bbox = font.getbbox(shaped)
        return bbox[2] - bbox[0]

    font_data = _get_font_bytes(font_path)
    hb_face = hb.Face(hb.Blob(font_data))
    hb_font = hb.Font(hb_face)
    hb_font.scale = (font_size * 64, font_size * 64)
    try:
        hb_font.set_variations({"wght": weight})
    except Exception:
        pass

    ft_face = _get_ft_face(font_path)
    ft_face.set_char_size(font_size * 64)
    try:
        ft_face.set_var_design_coords([weight, 0.0])
    except Exception:
        pass

    buf = hb.Buffer()
    buf.add_str(line)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)

    infos = buf.glyph_infos
    positions = buf.glyph_positions

    total_w = sum(pos.x_advance for pos in positions) // 64
    start_x = center_x - (total_w // 2)

    cur_x = start_x
    cur_y = baseline_y

    mode = target_image.mode
    for info, pos in zip(infos, positions):
        ft_face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
        glyph = ft_face.glyph
        bitmap = glyph.bitmap

        x = cur_x + (pos.x_offset // 64) + glyph.bitmap_left
        y = cur_y - (pos.y_offset // 64) - glyph.bitmap_top

        if bitmap.width > 0 and bitmap.rows > 0:
            mask = Image.frombytes("L", (bitmap.width, bitmap.rows), bytes(bitmap.buffer))
            color_img = Image.new(mode, (bitmap.width, bitmap.rows), color_hex)
            target_image.paste(color_img, (x, y), mask=mask)

        cur_x += pos.x_advance // 64
        cur_y -= pos.y_advance // 64

    return total_w
