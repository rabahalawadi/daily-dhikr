"""
Pytest configuration and reusable test fixtures.
Provides an isolated in-memory SQLite database, sample verified records,
and mocked external service dependencies.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys
import pytest

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import (
    SourceRecord,
    ContentItem,
    PublicationJob,
    SourceType,
    VerificationStatus,
    ApprovalStatus,
    ContentCategory,
    PublicationType,
    JobStatus,
)


@pytest.fixture(scope="function")
def db_session():
    """Yields a clean in-memory SQLite database session for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_verified_source(db_session):
    """Creates a verified Sahih Hadith source."""
    source = SourceRecord(
        source_type=SourceType.HADITH,
        source_name="Sahih al-Bukhari",
        reference="Hadith 6407",
        hadith_grade="Sahih",
        grading_source="Imam al-Bukhari",
        status=VerificationStatus.VERIFIED,
        verified_by="Scholar",
        verified_at=datetime.now(timezone.utc),
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


@pytest.fixture
def sample_approved_content(db_session, sample_verified_source):
    """Creates an approved and verified content item."""
    item = ContentItem(
        category=ContentCategory.DAILY_REMINDER,
        arabic_text="سُبْحَانَ اللَّهِ وَبِحَمْدِهِ",
        english_meaning="Glory be to Allah and His is the praise",
        transliteration="Subhan Allahi wa bihamdihi",
        source_id=sample_verified_source.id,
        verification_status=VerificationStatus.VERIFIED,
        approval_status=ApprovalStatus.APPROVED,
        is_demo=False,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def sample_demo_content(db_session, sample_verified_source):
    """Creates a demo-only content item that must be excluded from live publication."""
    item = ContentItem(
        category=ContentCategory.DAILY_REMINDER,
        arabic_text="ذِكْرٌ تَجْرِيبِيّ",
        english_meaning="Demo Test Reminder",
        source_id=sample_verified_source.id,
        verification_status=VerificationStatus.VERIFIED,
        approval_status=ApprovalStatus.APPROVED,
        is_demo=True,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item
