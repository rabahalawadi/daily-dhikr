"""
Unit tests for Daily Quran Verse Rotation, Friday Slot Adaptation, and Carousel Publishing.
"""

from datetime import date, datetime, timezone
import pytest

from app.models import (
    ContentItem,
    PublicationJob,
    ContentCategory,
    PublicationType,
    ApprovalStatus,
    VerificationStatus,
    SourceRecord,
    SourceType,
)
from app.scheduler.queue import select_rotating_content, schedule_daily_jobs
from app.scheduler.timezone import calculate_slot_datetimes
from app.publishing.instagrapi_client import InstagrapiPublisher
from app.publishing.instagram import InstagramPublisher


def test_daily_quran_rotation_selects_different_verses(db_session):
    """Verifies that select_rotating_content rotates through available verses without repeating."""
    source = SourceRecord(
        source_type=SourceType.QURAN,
        source_name="Test Surah",
        reference="1:1",
        status=VerificationStatus.VERIFIED,
    )
    db_session.add(source)
    db_session.flush()

    # Create 3 verses
    v1 = ContentItem(
        category=ContentCategory.VERSE_OF_THE_DAY,
        arabic_text="آية أولى تجريبية",
        english_meaning="First test verse",
        source_id=source.id,
        approval_status=ApprovalStatus.APPROVED,
        verification_status=VerificationStatus.VERIFIED,
    )
    v2 = ContentItem(
        category=ContentCategory.VERSE_OF_THE_DAY,
        arabic_text="آية ثانية تجريبية",
        english_meaning="Second test verse",
        source_id=source.id,
        approval_status=ApprovalStatus.APPROVED,
        verification_status=VerificationStatus.VERIFIED,
    )
    v3 = ContentItem(
        category=ContentCategory.VERSE_OF_THE_DAY,
        arabic_text="آية ثالثة تجريبية",
        english_meaning="Third test verse",
        source_id=source.id,
        approval_status=ApprovalStatus.APPROVED,
        verification_status=VerificationStatus.VERIFIED,
    )
    db_session.add_all([v1, v2, v3])
    db_session.commit()

    # First pick should pick v1
    pick1 = select_rotating_content(db_session, ContentCategory.VERSE_OF_THE_DAY)
    assert pick1.id == v1.id

    # Simulate scheduling pick1 in a publication job
    job1 = PublicationJob(
        content_id=pick1.id,
        platform="instagram",
        publication_type=PublicationType.FEED_POST,
        scheduled_at=datetime.now(timezone.utc),
    )
    db_session.add(job1)
    db_session.commit()

    # Second pick should pick v2
    pick2 = select_rotating_content(db_session, ContentCategory.VERSE_OF_THE_DAY)
    assert pick2.id == v2.id

    # Simulate scheduling pick2
    job2 = PublicationJob(
        content_id=pick2.id,
        platform="instagram",
        publication_type=PublicationType.FEED_POST,
        scheduled_at=datetime.now(timezone.utc),
    )
    db_session.add(job2)
    db_session.commit()

    # Third pick should pick v3
    pick3 = select_rotating_content(db_session, ContentCategory.VERSE_OF_THE_DAY)
    assert pick3.id == v3.id


def test_friday_slot_adaptation():
    """Verifies that on Friday (weekday 4), 09:00 slot is FRIDAY_SPECIAL, and on other days VERSE_OF_THE_DAY."""
    friday = date(2026, 10, 23)  # Friday
    saturday = date(2026, 10, 24)  # Saturday

    assert friday.weekday() == 4
    assert saturday.weekday() == 5

    friday_slots = calculate_slot_datetimes(friday)
    sat_slots = calculate_slot_datetimes(saturday)

    friday_feed = next(s for s in friday_slots if s["slot_name"] == "feed_post")
    sat_feed = next(s for s in sat_slots if s["slot_name"] == "feed_post")

    assert friday_feed["category"] == ContentCategory.FRIDAY_SPECIAL
    assert friday_feed["template"] == "surah_kahf_carousel"

    assert sat_feed["category"] == ContentCategory.VERSE_OF_THE_DAY
    assert sat_feed["template"] == "verse_of_the_day"


def test_instagrapi_publish_carousel_dry_run():
    """Verifies InstagrapiPublisher.publish_carousel in dry-run mode returns simulated ID without API call."""
    pub = InstagrapiPublisher(dry_run=True, publishing_enabled=True)
    fake_paths = ["assets/test1.png", "assets/test2.png"]
    res = pub.publish_carousel(fake_paths, "Test Friday Caption")
    assert res.startswith("dryrun_instagrapi_carousel_")


def test_official_publish_carousel_dry_run():
    """Verifies InstagramPublisher.create_carousel_media_container in dry-run mode returns simulated ID."""
    pub = InstagramPublisher(dry_run=True)
    fake_urls = ["https://example.com/1.png", "https://example.com/2.png"]
    res = pub.create_carousel_media_container(fake_urls, "Test Friday Caption")
    assert res.startswith("dryrun_container_carousel_")
