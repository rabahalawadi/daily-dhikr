"""
CLI tool for fetching and importing Quran verses from https://github.com/fawazahmed0/quran-api.
Supports syncing the curated short, impactful verses, importing specific chapter:verse items,
and rendering test graphics.
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db, get_db_context
from app.content.quran_api import (
    fetch_verse,
    is_short_and_meaningful,
    save_verse_to_db,
    sync_curated_verses,
    CURATED_SHORT_VERSES,
    SURAHS,
)
from app.graphics.renderer import renderer
from app.models import ContentItem, ContentCategory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Quran API Verse Ingestion CLI")
    parser.add_argument("--sync-curated", action="store_true", help="Fetch and sync all curated short verses")
    parser.add_argument("--chapter", type=int, help="Quran Surah number (1-114)")
    parser.add_argument("--verse", type=int, help="Ayah number in the Surah")
    parser.add_argument("--list", action="store_true", help="List all pre-curated short verses")
    parser.add_argument("--render-latest", action="store_true", help="Render Instagram graphics for imported verses")

    args = parser.parse_args()
    init_db()

    if args.list:
        print("=== PRE-CURATED SHORT & IMPACTFUL QURANIC VERSES ===")
        for ch, v in CURATED_SHORT_VERSES:
            s_info = SURAHS.get(ch, {})
            print(f"Surah {s_info.get('name_en')} ({s_info.get('name_ar')}) [{ch}:{v}]")
        return

    if args.sync_curated:
        print("Syncing curated short verses from Quran API...")
        with get_db_context() as db:
            items = sync_curated_verses(db, auto_approve=True)
            print(f"Successfully synced {len(items)} verses into the database.")
            for it in items:
                print(f"  • {it.source.source_name} [{it.source.reference}]: {it.arabic_text[:35]}...")
        return

    if args.chapter and args.verse:
        print(f"Fetching verse {args.chapter}:{args.verse} from Quran API...")
        verse_data = fetch_verse(args.chapter, args.verse)
        print("\n--- Verse Information ---")
        print(f"Surah: {verse_data['surah_name_en']} ({verse_data['surah_name_ar']}) [{args.chapter}:{args.verse}]")
        print(f"Arabic: {verse_data['arabic_text']}")
        print(f"English: {verse_data['english_meaning']}")
        print(f"Words: {verse_data['word_count']} | Chars: {verse_data['char_count']}")
        print(f"Is Short & Meaningful: {is_short_and_meaningful(verse_data)}")

        with get_db_context() as db:
            item = save_verse_to_db(db, verse_data, auto_approve=True)
            print(f"Saved into database with Item ID: {item.id}")

            if args.render_latest:
                feed_path, _, _, _ = renderer.render(item, template_name="verse_of_the_day")
                story_path, _, _, _ = renderer.render(item, template_name="verse_story")
                print(f"Rendered feed post: {feed_path}")
                print(f"Rendered story post: {story_path}")
        return

    if args.render_latest:
        with get_db_context() as db:
            items = (
                db.query(ContentItem)
                .filter(ContentItem.category == ContentCategory.VERSE_OF_THE_DAY)
                .all()
            )
            print(f"Rendering graphics for {len(items)} Verse of the Day items...")
            for it in items:
                feed_path, _, _, _ = renderer.render(it, template_name="verse_of_the_day")
                print(f"  Feed: {feed_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
