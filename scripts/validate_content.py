"""
Content and Source Verification Script.
Runs comprehensive validity checks on all items in the content library:
1. Arabic unicode validity & non-empty text.
2. English translation presence.
3. Source reference completeness according to Islamic scholarship rules.
4. Rendering test with Pillow to ensure text does not overflow or crash.
Used in CI/CD (.github/workflows/validate-content.yml).
"""

import sys
from pathlib import Path

# Ensure UTF-8 stdout for Windows consoles and Linux runners
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_db_context, init_db
from app.models import ContentItem, VerificationStatus, ApprovalStatus
from app.content.verification import validate_content_item
from app.graphics.renderer import renderer


def validate_all_content() -> int:
    init_db()
    errors_found = 0

    with get_db_context() as db:
        items = db.query(ContentItem).all()
        print(f"Validating {len(items)} content items in library...")

        for idx, item in enumerate(items, 1):
            item_id_short = item.id[:8]
            print(f"\n[{idx}/{len(items)}] Validating Item {item_id_short} ({item.category.value})...")

            # Check 1: Verification rules
            is_valid, errors = validate_content_item(item)
            if not is_valid:
                print(f"  ❌ Content validation errors:")
                for err in errors:
                    print(f"     - {err}")
                errors_found += 1
            else:
                print(f"  ✅ Source and text rules passed.")

            # Check 2: Render test on feed template
            try:
                img_path, checksum, w, h = renderer.render(item, template_name="feed_post")
                print(f"  ✅ Render check passed ({w}x{h}, sha256={checksum[:8]})")
            except Exception as e:
                print(f"  ❌ Render failed: {e}")
                errors_found += 1

            if item.is_demo:
                print(f"  ℹ️ Item flagged as DEMO (prohibited from publishing).")

    print("\n" + "=" * 50)
    if errors_found == 0:
        print(f"All content validated successfully with 0 errors!")
        return 0
    else:
        print(f"Validation failed with {errors_found} errors.")
        return 1


if __name__ == "__main__":
    sys.exit(validate_all_content())
