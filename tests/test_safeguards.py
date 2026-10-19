"""
Tests for Islamic content authenticity safeguards, approval gates, and demo exclusion.
"""

import pytest
from app.models import (
    SourceRecord,
    ContentItem,
    SourceType,
    VerificationStatus,
    ApprovalStatus,
    ContentCategory,
)
from app.content.verification import (
    validate_source,
    validate_content_item,
    can_be_published,
)


def test_demo_record_is_strictly_blocked(sample_demo_content):
    """Ensures records flagged as DEMO are blocked by the publish gatekeeper."""
    publishable, reason = can_be_published(sample_demo_content)
    assert publishable is False
    assert "DEMO" in reason


def test_unapproved_record_is_blocked(sample_approved_content):
    """Ensures draft or unapproved content cannot be published."""
    sample_approved_content.approval_status = ApprovalStatus.DRAFT
    publishable, reason = can_be_published(sample_approved_content)
    assert publishable is False
    assert "DRAFT" in reason


def test_unverified_record_is_blocked(sample_approved_content):
    """Ensures unverified content cannot be published."""
    sample_approved_content.verification_status = VerificationStatus.UNVERIFIED
    publishable, reason = can_be_published(sample_approved_content)
    assert publishable is False
    assert "UNVERIFIED" in reason


def test_quran_without_surah_or_ayah_fails_validation():
    """Quran citations must include Surah name and Ayah reference."""
    invalid_quran_source = SourceRecord(
        source_type=SourceType.QURAN,
        source_name="Noble Quran",
        reference="Random Page",  # Missing Surah or Ayah
        status=VerificationStatus.UNVERIFIED,
    )
    is_valid, errors = validate_source(invalid_quran_source)
    assert is_valid is False
    assert any("Surah and Ayah" in err for err in errors)


def test_hadith_without_grade_fails_validation():
    """Hadith citations must have a grade (Sahih, Hasan)."""
    invalid_hadith_source = SourceRecord(
        source_type=SourceType.HADITH,
        source_name="Sunan Abi Dawud",
        reference="Hadith 1234",
        hadith_grade=None,  # Missing grade
        status=VerificationStatus.UNVERIFIED,
    )
    is_valid, errors = validate_source(invalid_hadith_source)
    assert is_valid is False
    assert any("hadith grade" in err for err in errors)


def test_weak_hadith_is_rejected():
    """Fabricated or weak Hadith are prohibited from public reminder broadcast."""
    weak_source = SourceRecord(
        source_type=SourceType.HADITH,
        source_name="Collection",
        reference="Hadith 555",
        hadith_grade="Da'eef (Weak)",
        status=VerificationStatus.UNVERIFIED,
    )
    is_valid, errors = validate_source(weak_source)
    assert is_valid is False
    assert any("not acceptable" in err for err in errors)


def test_verified_authentic_item_passes(sample_approved_content):
    """Verifies that authentic, verified, approved content passes all checks."""
    publishable, reason = can_be_published(sample_approved_content)
    assert publishable is True
    assert reason is None
