"""
Pillow-based Graphic Rendering Engine for Daily Dhikr.
Renders high-contrast, elegant, mobile-optimized images with proper
Arabic text shaping, bidirectional layout, and Islamic geometric accents.
"""

import hashlib
import io
import logging
from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image, ImageDraw, ImageFont
from app.config import settings
from app.models import ContentItem, AssetType, ContentCategory, SourceType
from app.graphics.fonts import (
    shape_arabic_text,
    get_arabic_font,
    get_english_font,
    load_font,
    measure_arabic_harfbuzz,
    render_arabic_harfbuzz,
    HAS_HARFBUZZ,
)
from app.graphics.templates import get_template, TemplateConfig, FEED_POST_TEMPLATE
from app.content.captions import format_source_citation

logger = logging.getLogger(__name__)


def wrap_arabic_lines(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    font_path: Optional[Path] = None,
    font_size: Optional[int] = None,
) -> List[str]:
    """
    Wraps Arabic text into visual lines that fit within max_width.
    Splits into words and tests candidate line width using HarfBuzz when available,
    or Pillow bounding box fallback.
    Returns list of unshaped (raw) Arabic lines so HarfBuzz can perform full GPOS shaping.
    """
    words = text.strip().split()
    if not words:
        return []

    lines = []
    current_words = []

    arabic_font_path = font_path or settings.get_arabic_font_path()
    f_size = font_size or getattr(font, "size", 48)

    for word in words:
        test_words = current_words + [word]
        test_line = " ".join(test_words)

        if HAS_HARFBUZZ and arabic_font_path.exists():
            width = measure_arabic_harfbuzz(test_line, arabic_font_path, f_size)
        else:
            shaped_test = shape_arabic_text(test_line)
            bbox = font.getbbox(shaped_test)
            width = bbox[2] - bbox[0]

        if width <= max_width or not current_words:
            current_words.append(word)
        else:
            lines.append(" ".join(current_words))
            current_words = [word]

    if current_words:
        lines.append(" ".join(current_words))

    return lines


def wrap_english_lines(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int
) -> List[str]:
    """
    Wraps English text cleanly into lines that fit within max_width.
    """
    words = text.strip().split()
    if not words:
        return []

    lines = []
    current_words = []

    for word in words:
        test_words = current_words + [word]
        test_line = " ".join(test_words)
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width or not current_words:
            current_words.append(word)
        else:
            lines.append(" ".join(current_words))
            current_words = [word]

    if current_words:
        lines.append(" ".join(current_words))

    return lines


def draw_geometric_accent(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    center_y: int,
    size: int,
    color: str
) -> None:
    """Draws a subtle 8-pointed Islamic star accent (Rub el Hizb style)."""
    half = size // 2
    # First square
    draw.rectangle(
        [(center_x - half, center_y - half), (center_x + half, center_y + half)],
        outline=color,
        width=2
    )
    # Diamond (rotated square)
    diamond = [
        (center_x, center_y - int(half * 1.35)),
        (center_x + int(half * 1.35), center_y),
        (center_x, center_y + int(half * 1.35)),
        (center_x - int(half * 1.35), center_y),
    ]
    draw.polygon(diamond, outline=color, width=2)
    # Center dot
    draw.ellipse(
        [(center_x - 3, center_y - 3), (center_x + 3, center_y + 3)],
        fill=color
    )


class GraphicRenderer:
    """High-resolution image generator for Instagram feed posts and Stories."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.OUTPUT_MEDIA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(
        self,
        item: ContentItem,
        template_name: str = "feed_post"
    ) -> Tuple[Path, str, int, int]:
        """
        Renders an Instagram graphic for the content item using the specified template.
        Returns: (saved_image_path, sha256_checksum, width, height)
        """
        # Auto-route template based on content category and target media type
        effective_template = template_name

        # For story templates: route to specific category template
        if effective_template in ("morning_story", "story", "story_post"):
            if item.category == ContentCategory.EVENING_DHIKR:
                effective_template = "evening_story"
            elif item.category == ContentCategory.DUA:
                effective_template = "dua_story"
            elif item.category == ContentCategory.DAILY_REMINDER:
                effective_template = "short_reminder"
            elif item.category == ContentCategory.FRIDAY_SPECIAL:
                effective_template = "friday_reminder"
            elif item.category == ContentCategory.VERSE_OF_THE_DAY:
                effective_template = "verse_story"
            elif item.category == ContentCategory.MORNING_DHIKR:
                effective_template = "morning_story"

        # For feed post templates:
        elif effective_template in ("feed_post", "default"):
            if item.category == ContentCategory.VERSE_OF_THE_DAY:
                effective_template = "verse_of_the_day"
            elif item.category == ContentCategory.FRIDAY_SPECIAL:
                effective_template = "friday_reminder"

        template: TemplateConfig = get_template(effective_template)

        # 1. Create base canvas
        image = Image.new("RGB", (template.width, template.height), color=template.bg_color)
        draw = ImageDraw.Draw(image)

        # 2. Draw border frame
        if template.border_accent:
            margin = 35
            draw.rectangle(
                [(margin, margin), (template.width - margin, template.height - margin)],
                outline=template.accent_color,
                width=2
            )
            inner_margin = 45
            draw.rectangle(
                [(inner_margin, inner_margin), (template.width - inner_margin, template.height - inner_margin)],
                outline=template.primary_text_color,
                width=1
            )

        # 3. Load Fonts
        # Quran Verses -> Authentic Uthmanic Script (King Fahd Complex / UthmanicHafs)
        # Hadith / Adhkar / Reminders -> Cairo font
        is_quran = (
            item.category == ContentCategory.VERSE_OF_THE_DAY
            or (item.source and item.source.source_type == SourceType.QURAN)
        )
        if is_quran:
            content_arabic_font_path = settings.get_uthmanic_font_path()
        else:
            content_arabic_font_path = settings.get_cairo_font_path()

        cairo_font_path = settings.get_cairo_font_path()
        arabic_font = get_arabic_font(template.arabic_font_size, weight=450, font_path=content_arabic_font_path)
        english_font = get_english_font(template.english_font_size, weight=600)
        header_font = get_english_font(24, weight=600)
        citation_font = get_english_font(22, weight=550)
        tagline_font = get_arabic_font(26, weight=450, font_path=cairo_font_path)
        arabic_font_path = content_arabic_font_path

        max_text_width = template.width - 160

        # 4. Draw Header
        header_y = template.safe_margin_top
        draw_geometric_accent(draw, template.width // 2, header_y, size=24, color=template.accent_color)

        # English brand / category title
        draw.text(
            (template.width // 2, header_y + 40),
            template.header_title_en,
            font=header_font,
            fill=template.primary_text_color,
            anchor="mm"
        )

        # Arabic brand tagline (in Cairo font)
        if HAS_HARFBUZZ and cairo_font_path.exists():
            tagline_baseline = header_y + 80 + int(26 * 0.28)
            render_arabic_harfbuzz(
                target_image=image,
                line=template.header_title_ar,
                font_path=cairo_font_path,
                font_size=26,
                color_hex=template.accent_color,
                center_x=template.width // 2,
                baseline_y=tagline_baseline,
                weight=450.0,
            )
        else:
            shaped_header_ar = shape_arabic_text(template.header_title_ar)
            draw.text(
                (template.width // 2, header_y + 80),
                shaped_header_ar,
                font=tagline_font,
                fill=template.accent_color,
                anchor="mm"
            )

        # Decorative divider under header
        div_y = header_y + 115
        draw.line(
            [(template.width // 2 - 120, div_y), (template.width // 2 + 120, div_y)],
            fill=template.accent_color,
            width=2
        )

        # Check if authentic raw Madani Mushaf PNG exists (Same architecture as Surah Al-Kahf)
        raw_mushaf_png = None
        if is_quran and item.source and item.source.reference:
            ref_slug = item.source.reference.replace(":", "_")
            possible_path = settings.PROJECT_ROOT / "assets" / "verses" / "raw" / f"verse_{ref_slug}.png"
            if possible_path.exists():
                raw_mushaf_png = possible_path

        content_top = header_y + 140
        content_bottom = template.height - template.safe_margin_bottom - 80
        available_h = content_bottom - content_top

        if raw_mushaf_png:
            # 5a. Direct Madani Mushaf Calligraphy PNG Rendering
            from app.content.verse_raw_png import colorize_ayah_rgba
            with Image.open(raw_mushaf_png) as ayah_raw:
                colorized_ayah = colorize_ayah_rgba(ayah_raw, (36, 73, 54))

            en_font = get_english_font(template.english_font_size, weight=600)
            en_lines = wrap_english_lines(item.english_meaning, en_font, max_text_width) if item.english_meaning else []
            en_line_h = int(template.english_font_size * 1.45)
            content_en_h = (70 + len(en_lines) * en_line_h) if en_lines else 0

            max_ayah_h = available_h - content_en_h - 40
            scale_w = max_text_width / colorized_ayah.width
            scale_h = max_ayah_h / colorized_ayah.height if colorized_ayah.height > 0 else 1.0
            scale = min(scale_w, scale_h, 1.0)

            target_w = max(50, int(colorized_ayah.width * scale))
            target_h = max(20, int(colorized_ayah.height * scale))
            resized_ayah = colorized_ayah.resize((target_w, target_h), Image.Resampling.LANCZOS)

            total_h = target_h + content_en_h
            start_y = content_top + max(20, (available_h - total_h) // 2)

            ayah_x = (template.width - target_w) // 2
            image.paste(resized_ayah, (ayah_x, start_y), resized_ayah)
            current_y = start_y + target_h

            if en_lines:
                current_y += 30
                draw_geometric_accent(draw, template.width // 2, current_y, size=16, color=template.accent_color)
                draw.line([(template.width // 2 - 80, current_y), (template.width // 2 - 25, current_y)], fill=template.accent_color, width=1)
                draw.line([(template.width // 2 + 25, current_y), (template.width // 2 + 80, current_y)], fill=template.accent_color, width=1)
                current_y += 45

                for line in en_lines:
                    draw.text((template.width // 2, current_y), line, font=en_font, fill=template.secondary_text_color, anchor="mm")
                    current_y += en_line_h
        else:
            # 5b. Font-Based Layout Calculation with Adaptive Auto-Fitting (Fallback / Hadith)
            ar_size = template.arabic_font_size
            en_size = template.english_font_size

            while True:
                cur_ar_font = get_arabic_font(ar_size, weight=450)
                cur_en_font = get_english_font(en_size, weight=600)

                ar_lines = wrap_arabic_lines(
                    item.arabic_text,
                    cur_ar_font,
                    max_text_width,
                    font_path=arabic_font_path,
                    font_size=ar_size,
                )
                en_lines = wrap_english_lines(item.english_meaning, cur_en_font, max_text_width)

                ar_line_h = int(ar_size * 1.55)
                en_line_h = int(en_size * 1.45)
                content_en_h = (70 + len(en_lines) * en_line_h) if en_lines else 0
                total_content_h = (len(ar_lines) * ar_line_h) + content_en_h

                if total_content_h <= available_h or ar_size <= 36:
                    arabic_font = cur_ar_font
                    english_font = cur_en_font
                    arabic_lines = ar_lines
                    english_lines = en_lines
                    arabic_line_height = ar_line_h
                    english_line_height = en_line_h
                    final_ar_size = ar_size
                    break

                ar_size -= 3
                en_size = max(20, int(ar_size * (template.english_font_size / template.arabic_font_size)))

            start_y = content_top + max(20, (available_h - total_content_h) // 2)

            current_y = start_y
            for line in arabic_lines:
                if HAS_HARFBUZZ and arabic_font_path.exists():
                    baseline = current_y + int(final_ar_size * 0.28)
                    render_arabic_harfbuzz(
                        target_image=image,
                        line=line,
                        font_path=arabic_font_path,
                        font_size=final_ar_size,
                        color_hex=template.primary_text_color,
                        center_x=template.width // 2,
                        baseline_y=baseline,
                        weight=450.0,
                    )
                else:
                    draw.text(
                        (template.width // 2, current_y),
                        shape_arabic_text(line),
                        font=arabic_font,
                        fill=template.primary_text_color,
                        anchor="mm"
                    )
                current_y += arabic_line_height

            if english_lines:
                current_y += 20
                draw_geometric_accent(draw, template.width // 2, current_y, size=16, color=template.accent_color)
                draw.line(
                    [(template.width // 2 - 80, current_y), (template.width // 2 - 25, current_y)],
                    fill=template.accent_color,
                    width=1
                )
                draw.line(
                    [(template.width // 2 + 25, current_y), (template.width // 2 + 80, current_y)],
                    fill=template.accent_color,
                    width=1
                )
                current_y += 45

                for line in english_lines:
                    draw.text(
                        (template.width // 2, current_y),
                        line,
                        font=english_font,
                        fill=template.secondary_text_color,
                        anchor="mm"
                    )
                    current_y += english_line_height

        # 9. Render Footer & Source Citation
        footer_y = template.height - template.safe_margin_bottom
        citation_text = format_source_citation(item, for_image=True)
        draw.text(
            (template.width // 2, footer_y - 25),
            citation_text,
            font=citation_font,
            fill=template.accent_color,
            anchor="mm"
        )
        draw.text(
            (template.width // 2, footer_y + 15),
            "@DailyDhikr • A moment of remembrance, every day.",
            font=header_font,
            fill=template.primary_text_color,
            anchor="mm"
        )

        # 10. Save and calculate checksum
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95, optimize=True)
        img_bytes = buffer.getvalue()
        checksum = hashlib.sha256(img_bytes).hexdigest()

        filename = f"{template.name}_{item.id[:8]}_{checksum[:8]}.jpg"
        output_path = self.output_dir / filename

        with open(output_path, "wb") as f:
            f.write(img_bytes)

        logger.info(f"Rendered {template.name} ({template.width}x{template.height}) to {output_path}")
        return output_path, checksum, template.width, template.height


# Singleton renderer
renderer = GraphicRenderer()
