"""
Instagram Notes Manager.
Instagram Notes are 60-character status updates shared above Direct Message inboxes.
Because Meta does NOT offer a public Graph API endpoint for third-party automated Note posting,
this module prepares, formats, validates length (<= 60 chars), queues the daily Note,
and marks the job as AWAITING_MANUAL_ACTION with a copy-to-clipboard checklist.
"""

import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models import ContentItem, PublicationJob, JobStatus, PublicationType, AuditLog

logger = logging.getLogger(__name__)

MAX_NOTE_LENGTH = 60


def format_note_text(item: ContentItem) -> str:
    """
    Constructs a concise, impactful dhikr note text strictly within 60 characters.
    Example: 'سبحان الله وبحمده ✦ Subhan Allah'
    """
    # Prefer custom short Arabic or English caption if provided
    raw_ar = item.arabic_text.strip()
    raw_en = item.english_meaning.strip()

    # 1. Try bilingual if brief enough
    combined = f"{raw_ar} ✦ {raw_en}"
    if len(combined) <= MAX_NOTE_LENGTH:
        return combined

    # 2. Try pure Arabic dhikr
    if len(raw_ar) <= MAX_NOTE_LENGTH:
        return raw_ar

    # 3. Try pure English meaning
    if len(raw_en) <= MAX_NOTE_LENGTH:
        return raw_en

    # 4. Truncate safely with ellipsis
    return raw_ar[:MAX_NOTE_LENGTH - 3] + "..."


def prepare_daily_note_job(
    db: Session,
    job: PublicationJob,
) -> Tuple[bool, str, str]:
    """
    Validates and prepares an Instagram Note publication job.
    Transitions status to AWAITING_MANUAL_ACTION and records copyable text.
    """
    if not job.content:
        job.status = JobStatus.FAILED
        job.last_error = "Note job has no linked content."
        db.flush()
        return False, "", "Missing linked content"

    note_text = format_note_text(job.content)
    length = len(note_text)

    if length > MAX_NOTE_LENGTH:
        job.status = JobStatus.FAILED
        job.last_error = f"Note text exceeds maximum length of {MAX_NOTE_LENGTH} chars (length={length})."
        db.flush()
        return False, note_text, job.last_error

    # Transition job to AWAITING_MANUAL_ACTION
    job.status = JobStatus.AWAITING_MANUAL_ACTION
    job.last_error = f"Note prepared: '{note_text}'. Official Instagram API does not support automated Note posting; ready for manual post."
    db.flush()

    audit = AuditLog(
        action="NOTE_PREPARED",
        entity_type="publication_job",
        entity_id=job.id,
        details=f"Note prepared for manual action ({length} chars): {note_text}"
    )
    db.add(audit)
    db.flush()

    logger.info(f"Prepared Instagram Note for manual posting: '{note_text}' ({length}/{MAX_NOTE_LENGTH} chars)")
    return True, note_text, "Awaiting manual action"


def get_manual_note_instructions(note_text: str) -> str:
    """Returns a step-by-step checklist for the human operator to publish the Note."""
    return f"""
============================================================
INSTAGRAM NOTE PUBLICATION CHECKLIST
============================================================
Ready Note Content ({len(note_text)}/60 characters):
"{note_text}"

Steps to publish:
1. Open the Instagram app on your mobile device.
2. Tap the Messenger / Direct Message icon in the top right.
3. Tap on your profile photo at the top of your inbox ("Your note").
4. Paste the note text above.
5. Tap "Share".
6. In Daily Dhikr Dashboard or CLI, mark the job as PUBLISHED.
============================================================
""".strip()
