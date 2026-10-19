"""
Tests for Instagram Notes formatting, character limit enforcement, and manual-action workflows.
"""

from datetime import datetime, timezone
import pytest
from app.models import PublicationJob, PublicationType, JobStatus
from app.publishing.notes import (
    format_note_text,
    prepare_daily_note_job,
    get_manual_note_instructions,
    MAX_NOTE_LENGTH,
)


def test_note_character_limit_enforced(sample_approved_content):
    """Ensures that note text is strictly within 60 characters."""
    note = format_note_text(sample_approved_content)
    assert len(note) <= MAX_NOTE_LENGTH


def test_long_content_note_truncation(sample_approved_content):
    """Verifies that excessively long text is safely truncated with ellipsis."""
    sample_approved_content.arabic_text = "كَلِمَتَانِ خَفِيفَتَانِ عَلَى اللِّسَانِ ثَقِيلَتَانِ فِي الْمِيزَانِ حَبِيبَتَانِ إِلَى الرَّحْمَنِ: سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ"
    sample_approved_content.english_meaning = "Two words are light on the tongue, heavy on the balance, and beloved to the Most Merciful: Glory be to Allah and His is the praise, Glory be to Allah the Magnificent."

    note = format_note_text(sample_approved_content)
    assert len(note) <= MAX_NOTE_LENGTH
    assert note.endswith("...")


def test_prepare_note_job_sets_awaiting_manual_action(db_session, sample_approved_content):
    """Verifies that preparing a Note job marks it as AWAITING_MANUAL_ACTION."""
    job = PublicationJob(
        content_id=sample_approved_content.id,
        publication_type=PublicationType.NOTE,
        scheduled_at=datetime.now(timezone.utc),
        status=JobStatus.READY,
    )
    db_session.add(job)
    db_session.commit()

    ok, note_text, msg = prepare_daily_note_job(db_session, job)
    assert ok is True
    assert job.status == JobStatus.AWAITING_MANUAL_ACTION
    assert len(note_text) <= MAX_NOTE_LENGTH


def test_manual_note_instructions_contain_checklist():
    """Verifies that the human checklist includes all required steps."""
    instructions = get_manual_note_instructions("سُبْحَانَ اللَّهِ")
    assert "Direct Message" in instructions
    assert "Your note" in instructions
    assert "Share" in instructions
