"""
Tests for Asia/Amman timezone handling, daylight saving transitions, and due slots.
"""

from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pytest
from app.scheduler.timezone import (
    get_configured_timezone,
    get_current_local_time,
    to_utc,
    to_local,
    calculate_slot_datetimes,
)
from app.scheduler.queue import get_due_jobs
from app.models import PublicationJob, JobStatus, PublicationType


def test_timezone_is_zone_aware():
    """Verifies that the configured timezone is timezone-aware."""
    now = get_current_local_time()
    assert now.tzinfo is not None


def test_daily_slots_calculation():
    """Ensures all 5 daily slots are calculated for a given date with UTC translations."""
    target = date(2026, 10, 19)
    slots = calculate_slot_datetimes(target)

    assert len(slots) == 5
    slot_names = [s["slot_name"] for s in slots]
    assert "morning_story" in slot_names
    assert "feed_post" in slot_names
    assert "reminder_story" in slot_names
    assert "evening_story" in slot_names
    assert "daily_note" in slot_names

    # Check UTC conversion for Morning Story (07:00 Jordan -> 04:00 UTC)
    morning_slot = next(s for s in slots if s["slot_name"] == "morning_story")
    assert morning_slot["scheduled_local"].hour == 7
    assert morning_slot["scheduled_utc"].hour == 4


def test_catch_up_window_due_jobs(db_session, sample_approved_content):
    """
    Verifies that overdue jobs within catch-up window are retrieved,
    while future jobs or jobs older than catch-up window are not.
    """
    now_utc = datetime.now(timezone.utc)

    # Job 1: Due right now (scheduled 10 mins ago) -> SHOULD BE RETURNED
    job_due = PublicationJob(
        content_id=sample_approved_content.id,
        publication_type=PublicationType.FEED_POST,
        scheduled_at=now_utc - timedelta(minutes=10),
        status=JobStatus.READY,
    )
    db_session.add(job_due)

    # Job 2: Future job (scheduled in 2 hours) -> SHOULD NOT BE RETURNED
    job_future = PublicationJob(
        content_id=sample_approved_content.id,
        publication_type=PublicationType.STORY_POST,
        scheduled_at=now_utc + timedelta(hours=2),
        status=JobStatus.READY,
    )
    db_session.add(job_future)

    # Job 3: Way too old (scheduled 48 hours ago, outside 24h catch-up) -> SHOULD NOT BE RETURNED
    job_expired = PublicationJob(
        content_id=sample_approved_content.id,
        publication_type=PublicationType.STORY_POST,
        scheduled_at=now_utc - timedelta(hours=48),
        status=JobStatus.READY,
    )
    db_session.add(job_expired)

    db_session.commit()

    due_jobs = get_due_jobs(db_session, reference_time=now_utc, catch_up_hours=24)
    assert len(due_jobs) == 1
    assert due_jobs[0].id == job_due.id
