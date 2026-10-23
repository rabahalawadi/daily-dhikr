"""
Test script to generate 3 diverse, long, and deeply meaningful Quran verses.
Renders feed post graphics (1080x1350) with auto-fitting typography and displays captions.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import ContentItem, PublicationJob, ContentCategory, PublicationType
from app.graphics.renderer import renderer
from app.content.captions import generate_bilingual_caption


def generate_3_profound_verses():
    db = SessionLocal()

    # Target 3 distinct, profoundly meaningful verses across different Surahs:
    # 1. Surah Al-Baqarah 2:186 (Proximity of Allah & Answering Dua)
    # 2. Surah Az-Zumar 39:53 (Allah's Infinite Forgiveness & Mercy)
    # 3. Surah At-Talaq 65:3 (Tawakkul & Unexpected Sustenance)
    target_refs = ["2:186", "39:53", "65:3"]

    print("=== GENERATING 3 PROFOUND & DIVERSE QURAN VERSES ===\n")

    results = []
    for i, ref in enumerate(target_refs, 1):
        item = (
            db.query(ContentItem)
            .join(ContentItem.source)
            .filter(
                ContentItem.category == ContentCategory.VERSE_OF_THE_DAY,
                ContentItem.source.has(reference=ref)
            )
            .first()
        )

        if not item:
            print(f"Warning: Verse {ref} not found, falling back to any available verse.")
            item = db.query(ContentItem).filter(ContentItem.category == ContentCategory.VERSE_OF_THE_DAY).first()

        # Render graphic using verse_of_the_day template with adaptive auto-fitting
        img_path, checksum, w, h = renderer.render(item, template_name="verse_of_the_day")
        caption = generate_bilingual_caption(item)

        src_name = item.source.source_name if item.source else ""
        src_ref = item.source.reference if item.source else ""

        print(f"✦ Verse {i}:")
        print(f"  Surah / Ref: {src_name} [{src_ref}]")
        print(f"  Arabic     : {item.arabic_text}")
        print(f"  English    : {item.english_meaning}")
        print(f"  Rendered   : {img_path} ({w}x{h})")
        print(f"  Checksum   : {checksum[:16]}...")
        print()

        results.append({
            "day": i,
            "ref": f"{src_name} [{src_ref}]",
            "arabic": item.arabic_text,
            "english": item.english_meaning,
            "path": str(img_path),
            "caption": caption,
        })

    return results


if __name__ == "__main__":
    generate_3_profound_verses()
