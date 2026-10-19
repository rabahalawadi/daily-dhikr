"""
CLI entry point for the scheduled daily execution pipeline.
Executed by GitHub Actions (.github/workflows/daily-content.yml) or locally.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 stdout for Windows consoles and Linux runners
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import get_db_context, init_db
from app.scheduler.runner import runner
from app.scheduler.timezone import get_current_local_time


def main():
    parser = argparse.ArgumentParser(description="Daily Dhikr Instagram Automation Runner")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode (no API calls)")
    parser.add_argument("--date", type=str, help="Target date YYYY-MM-DD (defaults to today in Asia/Amman)")
    parser.add_argument("--seed", action="store_true", help="Seed database if empty before running")
    args = parser.parse_args()

    if args.dry_run:
        settings.DRY_RUN = True

    init_db()

    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    with get_db_context() as db:
        if args.seed:
            from scripts.seed_demo import seed
            seed()

        stats = runner.run(db, target_date=target_date)

    # If running inside GitHub Actions, write to GITHUB_STEP_SUMMARY
    github_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_summary_path:
        with open(github_summary_path, "a", encoding="utf-8") as f:
            f.write("## 🌙 Daily Dhikr Automation - Execution Summary\n\n")
            f.write(f"- **Local Date:** {target_date or get_current_local_time().date()}\n")
            f.write(f"- **Timezone:** `{settings.TIMEZONE}`\n")
            f.write(f"- **Feed Posts Published:** `{stats['feed_posts_published']}`\n")
            f.write(f"- **Stories Published:** `{stats['stories_published']}`\n")
            f.write(f"- **Notes Prepared:** `{stats['notes_prepared']}`\n")
            f.write(f"- **Jobs Skipped:** `{stats['jobs_skipped']}`\n")
            f.write(f"- **Jobs Failed:** `{stats['jobs_failed']}`\n\n")
            if stats["details"]:
                f.write("### Execution Details\n")
                for d in stats["details"]:
                    f.write(f"- {d}\n")

    # Meaningful exit code
    if stats["jobs_failed"] > 0:
        print(f"\nExecution finished with {stats['jobs_failed']} failed jobs.")
        sys.exit(1)

    print("\nExecution completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
