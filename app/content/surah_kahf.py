"""
Surat Al-Kahf Friday Automation Module for Daily Dhikr.
Manages downloading, rendering, and carousel preparation for all 12 pages (293-304)
of Surah Al-Kahf in authentic Madinah Mushaf Arabic script.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional
import urllib.request

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    SourceRecord,
    ContentItem,
    SourceType,
    VerificationStatus,
    ApprovalStatus,
    ContentCategory,
    AuditLog,
)
from app.graphics.fonts import (
    get_arabic_font,
    shape_arabic_text,
    measure_arabic_harfbuzz,
    render_arabic_harfbuzz,
    HAS_HARFBUZZ,
)

logger = logging.getLogger(__name__)

START_PAGE = 293
END_PAGE = 304
TOTAL_PAGES = END_PAGE - START_PAGE + 1  # 12 pages

SURAH_NAME_AR = "سُورَةُ الكَهْفِ"
SURAH_NAME_EN = "Surah Al-Kahf"

RAW_PAGES_DIR = settings.PROJECT_ROOT / "assets" / "surah_kahf" / "raw"
RENDERED_PAGES_DIR = settings.PROJECT_ROOT / "assets" / "surah_kahf" / "rendered"
GITHUB_RAW_URL_TEMPLATE = "https://raw.githubusercontent.com/GovarJabbar/Quran-PNG/master/{page}.png"


def to_arabic_indic_digits(num: int) -> str:
    """Converts a standard integer to Arabic-Indic digits (٠-٩)."""
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    return "".join(arabic_digits[int(d)] for d in str(num))


def download_kahf_pages() -> List[Path]:
    """
    Ensures all 12 Mushaf page PNGs (293 to 304) exist locally.
    Downloads any missing pages from the authentic Quran-PNG repository.
    """
    RAW_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    downloaded_paths = []

    for page in range(START_PAGE, END_PAGE + 1):
        target_path = RAW_PAGES_DIR / f"page_{page}.png"
        if not target_path.exists() or target_path.stat().st_size == 0:
            url = GITHUB_RAW_URL_TEMPLATE.format(page=page)
            logger.info(f"Downloading Surah Al-Kahf page {page} from {url}...")
            req = urllib.request.Request(url, headers={"User-Agent": "DailyDhikr/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                target_path.write_bytes(data)
            logger.info(f"Saved page {page} ({len(data)} bytes) to {target_path}")
        downloaded_paths.append(target_path)

    return downloaded_paths


def colorize_mushaf_rgba(
    img_rgba: Image.Image,
    color_rgb: Tuple[int, int, int] = (36, 73, 54)
) -> Image.Image:
    """
    Colorizes black calligraphy on transparent background into brand Forest Green (#244936)
    while perfectly preserving smooth anti-aliased alpha contours.
    """
    r, g, b, a = img_rgba.split()
    solid = Image.new("RGB", img_rgba.size, color_rgb)
    colored = solid.convert("RGBA")
    colored.putalpha(a)
    return colored


def render_kahf_page(
    page_num: int,
    raw_path: Path,
    output_path: Path,
    width: int = 1080,
    height: int = 1350,
) -> Path:
    """
    Renders an authentic Madinah Mushaf page into Daily Dhikr's 1080x1350 4:5 frame:
    - Cream background (#FAF8F1)
    - Gold and Forest Green geometric borders
    - Header: سُورَةُ الكَهْفِ
    - High-resolution scaled Mushaf text colored in brand Forest Green (#244936)
    - Bottom: Page indicator in Arabic (e.g. صفحة ٢٩٣ · ١ من ١٢)
    """
    canvas = Image.new("RGB", (width, height), settings.COLOR_CREAM)
    draw = ImageDraw.Draw(canvas)

    # 1. Elegant brand border
    border_gold = settings.COLOR_GOLD          # #B99A59
    border_green = settings.COLOR_FOREST_GREEN  # #244936
    draw.rectangle([20, 20, width - 20, height - 20], outline=border_gold, width=2)
    draw.rectangle([26, 26, width - 26, height - 26], outline=border_green, width=1)

    # 2. Header: سُورَةُ الكَهْفِ
    header_text = SURAH_NAME_AR
    cairo_font = get_arabic_font(42)
    arabic_font_path = settings.get_arabic_font_path()

    if HAS_HARFBUZZ and arabic_font_path.exists():
        render_arabic_harfbuzz(
            canvas,
            header_text,
            arabic_font_path,
            font_size=42,
            color_hex=border_green,
            center_x=width // 2,
            baseline_y=68,
        )
    else:
        shaped_header = shape_arabic_text(header_text)
        bbox = cairo_font.getbbox(shaped_header)
        hw = bbox[2] - bbox[0]
        hx = (width - hw) // 2
        draw.text((hx, 45), shaped_header, font=cairo_font, fill=border_green)

    # Decorative header divider
    draw.line([(width // 2 - 120, 95), (width // 2 + 120, 95)], fill=border_gold, width=2)

    # 3. Center: Mushaf Page Image with Colorized Text
    with Image.open(raw_path) as raw_img:
        mushaf_rgba = raw_img.convert("RGBA")
        # Colorize the calligraphy into brand Forest Green (#244936)
        mushaf_rgba = colorize_mushaf_rgba(mushaf_rgba, (36, 73, 54))

        if page_num == START_PAGE:
            # Page 293: Crop out previous verses of Surah Al-Isra' (y < 2845)
            # Retain only the Surah Al-Kahf header banner, Bismillah, and verses 1-4
            cropped_kahf = mushaf_rgba.crop((0, 2845, mushaf_rgba.width, 4102))

            # Scale to fit comfortably
            target_w = 980
            target_h = int(target_w * (cropped_kahf.height / cropped_kahf.width))
            resized_mushaf = cropped_kahf.resize((target_w, target_h), Image.Resampling.LANCZOS)

            # Center vertically in the middle of usable canvas area (between header and footer)
            usable_h = (height - 100) - 110
            mx = (width - target_w) // 2
            my = 110 + (usable_h - target_h) // 2
            canvas.paste(resized_mushaf, (mx, my), resized_mushaf)
        else:
            # Full pages (294 to 304)
            available_h = 1130
            available_w = 980
            aspect = mushaf_rgba.width / mushaf_rgba.height

            target_h = available_h
            target_w = int(target_h * aspect)
            if target_w > available_w:
                target_w = available_w
                target_h = int(target_w / aspect)

            resized_mushaf = mushaf_rgba.resize((target_w, target_h), Image.Resampling.LANCZOS)
            mx = (width - target_w) // 2
            my = 105 + (available_h - target_h) // 2
            canvas.paste(resized_mushaf, (mx, my), resized_mushaf)

    # 4. Footer: Arabic Page Indicator
    # Uses shape_arabic_text with Unicode BiDi reordering so digits (e.g. 12 and 304) are never reversed
    idx = page_num - START_PAGE + 1
    page_ar = to_arabic_indic_digits(page_num)
    idx_ar = to_arabic_indic_digits(idx)
    tot_ar = to_arabic_indic_digits(TOTAL_PAGES)
    footer_text = f"صفحة {page_ar}  ({idx_ar} من {tot_ar})  ·  ذكر يطمئن قلبك"

    footer_font = get_arabic_font(24)
    shaped_footer = shape_arabic_text(footer_text)
    draw.text((width // 2, height - 60), shaped_footer, font=footer_font, fill=border_green, anchor="mm")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG", optimize=True)
    return output_path


def render_kahf_carousel_pages(force_rerender: bool = False) -> List[Path]:
    """
    Renders all 12 pages of Surah Al-Kahf into 1080x1350 Instagram feed images.
    Returns list of 12 output image Paths.
    """
    raw_paths = download_kahf_pages()
    RENDERED_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    rendered_paths = []

    for i, raw_path in enumerate(raw_paths):
        page_num = START_PAGE + i
        out_path = RENDERED_PAGES_DIR / f"page_{page_num}.png"
        if force_rerender or not out_path.exists() or out_path.stat().st_size == 0:
            logger.info(f"Rendering Surah Al-Kahf page {page_num}...")
            render_kahf_page(page_num, raw_path, out_path)
        rendered_paths.append(out_path)

    return rendered_paths


KAHF_ARABIC_CAPTION = (
    "✦ سُورَةُ الكَهْفِ كَامِلَةً ✦\n\n"
    "قال رسول الله ﷺ:\n"
    "«مَنْ قَرَأَ سُورَةَ الْكَهْفِ فِي يَوْمِ الْجُمُعَةِ أَضَاءَ لَهُ مِنَ النُّورِ مَا بَيْنَ الْجُمُعَتَيْنِ»\n"
    "[صحيح الترغيب: 736]\n\n"
    "اسحب لقراءة صفحات سورة الكهف كاملة (١٢ صفحة) 📖✨\n"
    "اللهم صلِّ وسلِّم وبارك على نبينا محمد وعلى آله وصحبه أجمعين."
)


def get_or_create_kahf_content_item(db: Session) -> ContentItem:
    """
    Finds or creates the verified ContentItem for Friday Surat Al-Kahf carousel post.
    """
    ref_str = "18:1-110"
    source = (
        db.query(SourceRecord)
        .filter(
            SourceRecord.source_type == SourceType.QURAN,
            SourceRecord.reference == ref_str,
        )
        .first()
    )

    if not source:
        source = SourceRecord(
            source_type=SourceType.QURAN,
            source_name="سورة الكهف (Surah Al-Kahf)",
            reference=ref_str,
            verification_notes=(
                "Surah Al-Kahf complete 110 verses across 12 pages (293-304) "
                "of the authentic Madani Mushaf from the King Fahd Complex."
            ),
            verified_by="King Fahd Complex / Tanzil",
            status=VerificationStatus.VERIFIED,
        )
        db.add(source)
        db.flush()

    item = (
        db.query(ContentItem)
        .filter(
            ContentItem.source_id == source.id,
            ContentItem.category == ContentCategory.FRIDAY_SPECIAL,
        )
        .first()
    )

    if not item:
        item = ContentItem(
            category=ContentCategory.FRIDAY_SPECIAL,
            arabic_text="سُورَةُ الْكَهْفِ كَامِلَةً (الصَّفَحَات ٢٩٣ - ٣٠٤)",
            english_meaning="Surah Al-Kahf (The Cave) - Complete 12-page recitation for Friday.",
            caption_ar=KAHF_ARABIC_CAPTION,
            caption_en="",  # Explicitly Arabic only
            source_id=source.id,
            transliteration=None,
            is_demo=False,
            verification_status=VerificationStatus.VERIFIED,
            approval_status=ApprovalStatus.APPROVED,
        )
        db.add(item)
        db.flush()

        audit = AuditLog(
            action="CONTENT_CREATED",
            entity_type="content_item",
            entity_id=item.id,
            details="Created Friday Surat Al-Kahf complete 12-page carousel content item."
        )
        db.add(audit)
        db.commit()

    return item


def render_kahf_story_background(output_path: Optional[Path] = None) -> Path:
    """
    Renders an elegant 1080x1920 9:16 cover background for Instagram Story sharing:
    - Cream background (#FAF8F1)
    - Gold and Forest Green geometric borders with corner ornaments
    - Top: ✦ يَوْمُ الجُمُعَةِ ✦
    - Middle:
        * Authentic Madani Mushaf banner: سُورَةُ الكَهْفِ
        * جُمُعَةٌ مُبَارَكَة
        * Prominent, large CTA button: اضغط لتصفح السورة كاملة  ↗ (Press to see the surah)
        * Subtitle: تلاوة كاملة بالمصحف الشريف · ١٢ صفحة
    - Bottom:
        * Sahih Friday Hadith: « مَنْ قَرَأَ سُورَةَ الْكَهْفِ فِي يَوْمِ الْجُمُعَةِ أَضَاءَ لَهُ مِنَ النُّورِ مَا بَيْنَ الْجُمُعَتَيْنِ »
        * Reference: رواه الحاكم والبيهقي · صحيح
    """
    width, height = 1080, 1920
    canvas = Image.new("RGB", (width, height), settings.COLOR_CREAM)
    draw = ImageDraw.Draw(canvas)

    border_gold = settings.COLOR_GOLD          # #B99A59
    border_green = settings.COLOR_FOREST_GREEN  # #244936

    # 1. Double border with corner accents
    draw.rectangle([30, 30, width - 30, height - 30], outline=border_gold, width=2)
    draw.rectangle([38, 38, width - 38, height - 38], outline=border_green, width=1)

    for cx, cy in [(30, 30), (width - 30, 30), (30, height - 30), (width - 30, height - 30)]:
        draw.rectangle([cx - 5, cy - 5, cx + 5, cy + 5], fill=border_gold)

    # 2. Top Header Emblem
    top_tag = "✦  يَوْمُ الجُمُعَةِ  ✦"
    cairo_top = get_arabic_font(32)
    draw.text((width // 2, 175), shape_arabic_text(top_tag), font=cairo_top, fill=border_gold, anchor="mm")

    # 3. Middle Section: Authentic Mushaf Title / Banner
    raw_page_293 = RAW_PAGES_DIR / "page_293.png"
    banner_drawn = False
    if raw_page_293.exists():
        try:
            with Image.open(raw_page_293) as raw_img:
                banner = raw_img.crop((100, 2855, raw_img.width - 100, 3320))
                banner_rgba = colorize_mushaf_rgba(banner.convert("RGBA"), (36, 73, 54))
                bw = 880
                bh = int(bw * (banner_rgba.height / banner_rgba.width))
                resized_banner = banner_rgba.resize((bw, bh), Image.Resampling.LANCZOS)
                bx = (width - bw) // 2
                by = 640
                canvas.paste(resized_banner, (bx, by), resized_banner)
                banner_drawn = True
        except Exception as e:
            logger.warning(f"Could not crop Mushaf banner: {e}")

    if not banner_drawn:
        # Fallback to typography title
        header_text = SURAH_NAME_AR
        arabic_font_path = settings.get_arabic_font_path()
        if HAS_HARFBUZZ and arabic_font_path.exists():
            render_arabic_harfbuzz(
                canvas, header_text, arabic_font_path, font_size=82,
                color_hex=border_green, center_x=width // 2, baseline_y=710
            )
        else:
            cairo_title = get_arabic_font(82)
            draw.text((width // 2, 680), shape_arabic_text(header_text), font=cairo_title, fill=border_green, anchor="mm")
        draw.line([(width // 2 - 160, 755), (width // 2 + 160, 755)], fill=border_gold, width=2)

    # Subtitle under banner
    friday_greeting = "جُمُعَةٌ مُبَارَكَة"
    cairo_greet = get_arabic_font(44)
    draw.text((width // 2, 880), shape_arabic_text(friday_greeting), font=cairo_greet, fill=border_green, anchor="mm")

    # Central Prominent Button: ( Press to see the surah )
    btn_w, btn_h = 780, 120
    btn_x0 = (width - btn_w) // 2
    btn_y0 = 960
    btn_x1 = btn_x0 + btn_w
    btn_y1 = btn_y0 + btn_h

    # Luxury pill background with gold border
    draw.rounded_rectangle([btn_x0, btn_y0, btn_x1, btn_y1], radius=60, fill="#F4EDE0", outline=border_gold, width=2)

    cta_text = "اضغط لتصفح السورة كاملة  ↗"
    cairo_cta = get_arabic_font(42)
    draw.text((width // 2, btn_y0 + btn_h // 2), shape_arabic_text(cta_text), font=cairo_cta, fill=border_green, anchor="mm")

    # Subtext under button
    sub_desc = "تلاوة كاملة بالمصحف الشريف  ·  ١٢ صفحة"
    cairo_desc = get_arabic_font(26)
    draw.text((width // 2, btn_y1 + 45), shape_arabic_text(sub_desc), font=cairo_desc, fill=border_gold, anchor="mm")

    # 4. Bottom Section: Friday Hadith
    hadith_l1 = "« مَنْ قَرَأَ سُورَةَ الْكَهْفِ فِي يَوْمِ الْجُمُعَةِ »"
    hadith_l2 = "« أَضَاءَ لَهُ مِنَ النُّورِ مَا بَيْنَ الْجُمُعَتَيْنِ »"
    hadith_src = "رواه الحاكم والبيهقي  ·  صحيح"

    cairo_hadith = get_arabic_font(30)
    cairo_src = get_arabic_font(22)

    draw.text((width // 2, height - 260), shape_arabic_text(hadith_l1), font=cairo_hadith, fill=border_green, anchor="mm")
    draw.text((width // 2, height - 215), shape_arabic_text(hadith_l2), font=cairo_hadith, fill=border_green, anchor="mm")
    draw.text((width // 2, height - 160), shape_arabic_text(hadith_src), font=cairo_src, fill=border_gold, anchor="mm")

    out = output_path or (RENDERED_PAGES_DIR / "kahf_story_background.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "PNG", optimize=True)
    return out

