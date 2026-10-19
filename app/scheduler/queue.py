"""
Persistent Publication Queue and Atomic Job Claiming Engine.
Guarantees exactly-once processing, prevents duplicate posts across concurrent runners,
and filters out unverified, unapproved, or demo content.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, update
from app.config import settings
from app.models import (
    PublicationJob,
    ContentItem,
    JobStatus,
    ApprovalStatus,
    VerificationStatus,
    AuditLog,
)
from app.scheduler.timezone import get_current_local_time, calculate_slot_datetimes

logger = logging.getLogger(__name__)


def get_due_jobs(
    db: Session,
    reference_time: Optional[datetime] = None,
    catch_up_hours: Optional[int] = None,
) -> List[PublicationJob]:
    """
    Finds all eligible publication jobs that are due for execution.
    Only returns jobs that:
    1. Have status in (READY, SCHEDULED).
    2. Have scheduled_at <= reference_time.
    3. Are within the catch-up window (scheduled_at >= reference_time - catch_up_hours).
    4. Are linked to verified, approved, non-demo content.
    """
    now_utc = reference_time.astimezone(timezone.utc) if reference_time else datetime.now(timezone.utc)
    window_hours = catch_up_hours if catch_up_hours is not None else settings.CATCH_UP_WINDOW_HOURS
    window_start = now_utc - timedelta(hours=window_hours)

    query = (
        db.query(PublicationJob)
        .join(PublicationJob.content)
        .filter(
            PublicationJob.status.in_([JobStatus.READY, JobStatus.SCHEDULED]),
            PublicationJob.scheduled_at <= now_utc,
            PublicationJob.scheduled_at >= window_start,
            ContentItem.approval_status == ApprovalStatus.APPROVED,
            ContentItem.verification_status == VerificationStatus.VERIFIED,
            ContentItem.is_demo == False,  # Strict safeguard: Demo records never published
        )
        .order_by(PublicationJob.scheduled_at.asc())
    )

    return query.all()


def claim_job_atomically(db: Session, job_id: str) -> bool:
    """
    Atomically claims a due job in the database.
    Transitions status from (READY, SCHEDULED) to PROCESSING.
    Returns True if successfully claimed, or False if another runner claimed it first.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        update(PublicationJob)
        .where(
            and_(
                PublicationJob.id == job_id,
                PublicationJob.status.in_([JobStatus.READY, JobStatus.SCHEDULED]),
            )
        )
        .values(
            status=JobStatus.PROCESSING,
            claimed_at=now,
            updated_at=now,
        )
    )

    result = db.execute(stmt)
    db.commit()

    claimed = result.rowcount == 1
    if claimed:
        audit = AuditLog(
            action="JOB_CLAIMED",
            entity_type="publication_job",
            entity_id=job_id,
            details=f"Job {job_id} atomically claimed for execution at {now.isoformat()}"
        )
        db.add(audit)
        db.commit()
        logger.info(f"Successfully claimed job {job_id}")
    else:
        logger.warning(f"Could not claim job {job_id} (already claimed or status changed)")

    return claimed


def schedule_daily_jobs(db: Session, target_date=None) -> List[PublicationJob]:
    """
    Ensures that publication jobs are scheduled for all daily slots on target_date.
    Selects approved, verified content for each slot and attaches it.
    """
    slots = calculate_slot_datetimes(target_date)
    created_jobs = []

    for slot in slots:
        # Check if a job already exists for this slot time and type
        existing = (
            db.query(PublicationJob)
            .filter(
                PublicationJob.publication_type == slot["pub_type"],
                PublicationJob.scheduled_at == slot["scheduled_utc"],
            )
            .first()
        )
        if existing:
            continue

        # Find an approved, verified, non-demo content item matching the category
        content_item = (
            db.query(ContentItem)
            .filter(
                ContentItem.approval_status == ApprovalStatus.APPROVED,
                ContentItem.verification_status == VerificationStatus.VERIFIED,
                ContentItem.is_demo == False,
                ContentItem.category == slot["category"],
            )
            .first()
        )

        if not content_item:
            # Try any general approved reminder if specific category not found
            content_item = (
                db.query(ContentItem)
                .filter(
                    ContentItem.approval_status == ApprovalStatus.APPROVED,
                    ContentItem.verification_status == VerificationStatus.VERIFIED,
                    ContentItem.is_demo == False,
                )
                .first()
            )

        if not content_item:
            logger.warning(f"No approved verified content available to schedule slot '{slot['slot_name']}'.")
            continue

        job = PublicationJob(
            content_id=content_item.id,
            platform="instagram",
            publication_type=slot["pub_type"],
            scheduled_at=slot["scheduled_utc"],
            status=JobStatus.READY,
        )
        db.add(job)
        db.flush()

        audit = AuditLog(
            action="JOB_SCHEDULED",
            entity_type="publication_job",
            entity_id=job.id,
            details=f"Scheduled slot '{slot['slot_name']}' for {slot['scheduled_local'].isoformat()}"
        )
        db.add(audit)
        created_jobs.append(job)

    db.commit()
    logger.info(f"Scheduled {len(created_jobs)} jobs for {target_date or 'today'}")
    return created_jobs
