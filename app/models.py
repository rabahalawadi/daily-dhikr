"""
SQLAlchemy ORM models for Daily Dhikr persistent storage.
Includes tables for content library, verified sources, media assets,
publication state machine jobs, retry attempts, app settings, and audit logs.
"""

import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceType(str, enum.Enum):
    QURAN = "QURAN"
    HADITH = "HADITH"
    ADHKAR_COLLECTION = "ADHKAR_COLLECTION"
    OTHER = "OTHER"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ApprovalStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ContentCategory(str, enum.Enum):
    MORNING_DHIKR = "MORNING_DHIKR"
    EVENING_DHIKR = "EVENING_DHIKR"
    DAILY_REMINDER = "DAILY_REMINDER"
    DUA = "DUA"
    FRIDAY_SPECIAL = "FRIDAY_SPECIAL"
    VERSE_OF_THE_DAY = "VERSE_OF_THE_DAY"
    NOTE = "NOTE"


class AssetType(str, enum.Enum):
    FEED_IMAGE = "FEED_IMAGE"
    STORY_IMAGE = "STORY_IMAGE"


class PublicationType(str, enum.Enum):
    FEED_POST = "FEED_POST"
    STORY_POST = "STORY_POST"
    NOTE = "NOTE"


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    APPROVED = "APPROVED"
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    PROCESSING = "PROCESSING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    AWAITING_MANUAL_ACTION = "AWAITING_MANUAL_ACTION"


class SourceRecord(Base):
    __tablename__ = "source_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_type = Column(Enum(SourceType), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    reference = Column(String(255), nullable=False)
    hadith_grade = Column(String(100), nullable=True)
    grading_source = Column(String(255), nullable=True)
    verification_notes = Column(Text, nullable=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    content_items = relationship("ContentItem", back_populates="source", cascade="all, delete-orphan")


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category = Column(Enum(ContentCategory), nullable=False, index=True)
    arabic_text = Column(Text, nullable=False)
    english_meaning = Column(Text, nullable=False)
    transliteration = Column(Text, nullable=True)
    caption_ar = Column(Text, nullable=True)
    caption_en = Column(Text, nullable=True)
    source_id = Column(String(36), ForeignKey("source_records.id"), nullable=False, index=True)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED, nullable=False, index=True)
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.DRAFT, nullable=False, index=True)
    is_demo = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    source = relationship("SourceRecord", back_populates="content_items")
    media_assets = relationship("MediaAsset", back_populates="content", cascade="all, delete-orphan")
    jobs = relationship("PublicationJob", back_populates="content", cascade="all, delete-orphan")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    content_id = Column(String(36), ForeignKey("content_items.id"), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    storage_url = Column(String(1024), nullable=False)
    local_path = Column(String(512), nullable=True)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=False, index=True)  # SHA256 of image bytes
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    content = relationship("ContentItem", back_populates="media_assets")


class PublicationJob(Base):
    __tablename__ = "publication_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    content_id = Column(String(36), ForeignKey("content_items.id"), nullable=False, index=True)
    platform = Column(String(50), default="instagram", nullable=False)
    publication_type = Column(Enum(PublicationType), nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT, nullable=False, index=True)
    attempt_count = Column(Integer, default=0, nullable=False)
    instagram_media_id = Column(String(100), nullable=True, index=True)
    last_error = Column(Text, nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    content = relationship("ContentItem", back_populates="jobs")
    attempts = relationship("PublicationAttempt", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_publication_jobs_due", "status", "scheduled_at"),
    )


class PublicationAttempt(Base):
    __tablename__ = "publication_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("publication_jobs.id"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    request_started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    response_received_at = Column(DateTime(timezone=True), nullable=True)
    response_status = Column(Integer, nullable=True)
    error_category = Column(String(50), nullable=True)
    error_message_redacted = Column(Text, nullable=True)

    job = relationship("PublicationJob", back_populates="attempts")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    details = Column(Text, nullable=True)
