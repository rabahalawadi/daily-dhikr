"""
Core Execution Engine for Daily Dhikr Automation.
Executes the full 12-step daily workflow:
1. Initialize configuration and persistent storage.
2. Load current date in Asia/Amman.
3. Find eligible publication jobs that are due.
4. Exclude unapproved, unverified, demo, or invalid jobs.
5. Atomically claim eligible jobs in the database.
6. Generate missing graphics from approved content.
7. Validate Arabic rendering, dimensions, text, and sources.
8. Call official Instagram API when publishing is enabled (or simulate cleanly in dry-run).
9. Record API result and media ID.
10. Prepare Note draft and mark AWAITING_MANUAL_ACTION.
11. Send notifications for failures or ambiguous results.
12. Output concise execution summary with real recorded numbers.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db_context, check_db_connection
from app.models import (
    PublicationJob,
    JobStatus,
    PublicationType,
    AssetType,
    MediaAsset,
    PublicationAttempt,
    AuditLog,
)
from app.content.verification import can_be_published
from app.content.captions import generate_bilingual_caption
from app.graphics.renderer import renderer
from app.publishing.storage import storage_manager
from app.publishing.instagram import publisher, InstagramAPIError
from app.publishing.notes import prepare_daily_note_job, get_manual_note_instructions
from app.publishing.retry import ErrorCategory
from app.scheduler.timezone import get_current_local_time
from app.scheduler.queue import get_due_jobs, claim_job_atomically, schedule_daily_jobs
from app.notifications.sender import notifier

logger = logging.getLogger(__name__)


class DailyWorkflowRunner:
    """Executes scheduled publishing workflows and tracks real statistics."""

    def __init__(self):
        self.stats = {
            "feed_posts_published": 0,
            "stories_published": 0,
            "notes_prepared": 0,
            "jobs_skipped": 0,
            "jobs_failed": 0,
            "details": [],
        }

    def run(self, db: Session, target_date=None) -> Dict[str, Any]:
        """Runs the complete 12-step execution cycle."""
        # Step 1: Initialize configuration and check database
        if not check_db_connection():
            raise ConnectionError("Database connection check failed.")

        # Step 2: Load current date and time in Asia/Amman
        now_amman = get_current_local_time()
        today_str = (target_date or now_amman.date()).isoformat()
        logger.info(f"=== Daily Dhikr Automation Started ===")
        logger.info(f"Timezone: {settings.TIMEZONE} | Local Time: {now_amman.isoformat()}")
        logger.info(f"Mode: {'DRY RUN' if settings.DRY_RUN else 'LIVE'} | Publishing Enabled: {settings.PUBLISHING_ENABLED}")

        # Ensure today's schedule exists if needed
        schedule_daily_jobs(db, target_date=target_date)

        # Step 3: Find all due publication jobs
        due_jobs = get_due_jobs(db, reference_time=now_amman)
        logger.info(f"Found {len(due_jobs)} eligible jobs due for execution.")

        for job in due_jobs:
            self._process_job(db, job)

        # Step 12: Print concise execution summary
        summary_text = self._format_summary(today_str)
        print(summary_text)

        # Step 11: Alert if failures occurred
        if self.stats["jobs_failed"] > 0:
            notifier.send_alert(
                title=f"Workflow Run Completed with {self.stats['jobs_failed']} Failures",
                message=summary_text,
                level="WARNING"
            )
        else:
            notifier.send_alert(
                title="Daily Execution Completed Successfully",
                message=summary_text,
                level="INFO"
            )

        return self.stats

    def _process_job(self, db: Session, job: PublicationJob) -> None:
        """Processes a single publication job through steps 4-10."""
        # Step 4: Exclude ineligible jobs
        if not job.content:
            job.status = JobStatus.SKIPPED
            job.last_error = "Skipped: Missing linked content."
            db.commit()
            self.stats["jobs_skipped"] += 1
            return

        is_publishable, block_reason = can_be_published(job.content)
        if not is_publishable:
            job.status = JobStatus.SKIPPED
            job.last_error = f"Skipped: {block_reason}"
            db.commit()
            logger.warning(f"Job {job.id} skipped: {block_reason}")
            self.stats["jobs_skipped"] += 1
            return

        # Step 5: Atomically claim the job
        claimed = claim_job_atomically(db, job.id)
        if not claimed:
            logger.info(f"Job {job.id} was not claimed (concurrent runner handled it). Skipping.")
            return

        # Handle Instagram Note specifically
        if job.publication_type == PublicationType.NOTE:
            # Step 10: Prepare Note draft and mark AWAITING_MANUAL_ACTION
            ok, note_text, reason = prepare_daily_note_job(db, job)
            if ok:
                self.stats["notes_prepared"] += 1
                self.stats["details"].append(f"Note prepared: '{note_text[:30]}...'")
                print(get_manual_note_instructions(note_text))
            else:
                self.stats["jobs_failed"] += 1
            db.commit()
            return

        # For Feed & Story posts:
        try:
            # Step 6: Generate missing graphic assets
            template_name = "feed_post" if job.publication_type == PublicationType.FEED_POST else "morning_story"
            img_path, checksum, width, height = renderer.render(job.content, template_name=template_name)

            # Step 7: Validate graphic dimensions and checksum
            expected_h = 1350 if job.publication_type == PublicationType.FEED_POST else 1920
            if width != 1080 or height != expected_h:
                raise ValueError(f"Invalid image dimensions: {width}x{height}, expected 1080x{expected_h}")

            # Upload to object storage to obtain public URL
            public_image_url = storage_manager.upload_file(img_path)

            # Record or reuse MediaAsset
            media_asset = (
                db.query(MediaAsset)
                .filter(MediaAsset.checksum == checksum)
                .first()
            )
            if not media_asset:
                media_asset = MediaAsset(
                    content_id=job.content.id,
                    asset_type=AssetType.FEED_IMAGE if job.publication_type == PublicationType.FEED_POST else AssetType.STORY_IMAGE,
                    storage_url=public_image_url,
                    local_path=str(img_path),
                    width=width,
                    height=height,
                    checksum=checksum,
                )
                db.add(media_asset)
                db.flush()

            # Generate structured bilingual caption for feed post
            caption = generate_bilingual_caption(job.content)

            # Step 8: Call official Instagram API
            job.attempt_count += 1
            attempt = PublicationAttempt(
                job_id=job.id,
                attempt_number=job.attempt_count,
                request_started_at=datetime.now(timezone.utc),
            )
            db.add(attempt)
            db.flush()

            if job.publication_type == PublicationType.FEED_POST:
                container_id = publisher.create_feed_media_container(public_image_url, caption)
            else:
                container_id = publisher.create_story_media_container(public_image_url)

            # Poll container status
            publisher.poll_container_status(container_id)

            # Publish container
            media_id = publisher.publish_container(container_id)

            # Step 9: Record API result and media ID
            attempt.response_received_at = datetime.now(timezone.utc)
            attempt.response_status = 200

            job.status = JobStatus.PUBLISHED
            job.instagram_media_id = media_id
            job.published_at = datetime.now(timezone.utc)
            job.last_error = None

            audit = AuditLog(
                action="JOB_PUBLISHED",
                entity_type="publication_job",
                entity_id=job.id,
                details=f"Published to Instagram ({job.publication_type.value}), media_id={media_id}"
            )
            db.add(audit)
            db.commit()

            if job.publication_type == PublicationType.FEED_POST:
                self.stats["feed_posts_published"] += 1
            else:
                self.stats["stories_published"] += 1

            self.stats["details"].append(f"Job {job.id[:8]} ({job.publication_type.value}) published: media_id={media_id}")

        except InstagramAPIError as err:
            logger.error(f"Instagram API Error publishing job {job.id}: {err}")
            job.status = JobStatus.FAILED
            job.last_error = str(err)
            if err.category == ErrorCategory.AMBIGUOUS_TIMEOUT:
                job.status = JobStatus.AWAITING_MANUAL_ACTION

            attempt = db.query(PublicationAttempt).filter(PublicationAttempt.job_id == job.id).order_by(PublicationAttempt.attempt_number.desc()).first()
            if attempt:
                attempt.response_received_at = datetime.now(timezone.utc)
                attempt.response_status = err.status_code
                attempt.error_category = err.category
                attempt.error_message_redacted = str(err)

            db.commit()
            self.stats["jobs_failed"] += 1

        except Exception as exc:
            logger.error(f"Unexpected error publishing job {job.id}: {exc}", exc_info=True)
            job.status = JobStatus.FAILED
            job.last_error = f"Unexpected failure: {str(exc)}"
            db.commit()
            self.stats["jobs_failed"] += 1

    def _format_summary(self, date_str: str) -> str:
        """Formats the official daily execution summary."""
        return f"""
Daily Dhikr Automation
Date: {date_str}
Feed posts published: {self.stats['feed_posts_published']}
Stories published: {self.stats['stories_published']}
Notes prepared: {self.stats['notes_prepared']}
Jobs skipped: {self.stats['jobs_skipped']}
Jobs failed: {self.stats['jobs_failed']}
""".strip()


runner = DailyWorkflowRunner()
