"""
Tests for database atomic claiming, duplicate prevention, and state transitions.
"""

from datetime import datetime, timezone
import pytest
from app.models import PublicationJob, JobStatus, PublicationType, AuditLog
from app.scheduler.queue import claim_job_atomically


def test_atomic_job_claiming_success(db_session, sample_approved_content):
    """Verifies that an unclaimed READY job is atomically transitioned to PROCESSING."""
    job = PublicationJob(
        content_id=sample_approved_content.id,
        publication_type=PublicationType.FEED_POST,
        scheduled_at=datetime.now(timezone.utc),
        status=JobStatus.READY,
    )
    db_session.add(job)
    db_session.commit()

    claimed = claim_job_atomically(db_session, job.id)
    assert claimed is True

    db_session.refresh(job)
    assert job.status == JobStatus.PROCESSING
    assert job.claimed_at is not None


def test_duplicate_claiming_prevention(db_session, sample_approved_content):
    """
    Critical concurrency safeguard:
    When a second worker attempts to claim an already claimed job, it must fail.
    """
    job = PublicationJob(
        content_id=sample_approved_content.id,
        publication_type=PublicationType.FEED_POST,
        scheduled_at=datetime.now(timezone.utc),
        status=JobStatus.READY,
    )
    db_session.add(job)
    db_session.commit()

    # First runner claims
    first_claim = claim_job_atomically(db_session, job.id)
    assert first_claim is True

    # Second concurrent runner attempts to claim the same job
    second_claim = claim_job_atomically(db_session, job.id)
    assert second_claim is False


def test_already_published_jobs_cannot_be_claimed(db_session, sample_approved_content):
    """Ensures jobs that have already been PUBLISHED cannot be re-claimed."""
    job = PublicationJob(
        content_id=sample_approved_content.id,
        publication_type=PublicationType.FEED_POST,
        scheduled_at=datetime.now(timezone.utc),
        status=JobStatus.PUBLISHED,
        instagram_media_id="ig_123456",
    )
    db_session.add(job)
    db_session.commit()

    claimed = claim_job_atomically(db_session, job.id)
    assert claimed is False
