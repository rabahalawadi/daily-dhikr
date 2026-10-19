"""
Pydantic schemas for request validation and serialization.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.models import (
    SourceType,
    VerificationStatus,
    ApprovalStatus,
    ContentCategory,
    AssetType,
    PublicationType,
    JobStatus,
)


class SourceRecordBase(BaseModel):
    source_type: SourceType
    source_name: str = Field(..., max_length=255)
    reference: str = Field(..., max_length=255)
    hadith_grade: Optional[str] = Field(None, max_length=100)
    grading_source: Optional[str] = Field(None, max_length=255)
    verification_notes: Optional[str] = None
    verified_by: Optional[str] = Field(None, max_length=100)


class SourceRecordCreate(SourceRecordBase):
    pass


class SourceRecordResponse(SourceRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: VerificationStatus
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ContentItemBase(BaseModel):
    category: ContentCategory
    arabic_text: str
    english_meaning: str
    transliteration: Optional[str] = None
    caption_ar: Optional[str] = None
    caption_en: Optional[str] = None
    source_id: str
    is_demo: bool = False


class ContentItemCreate(ContentItemBase):
    pass


class ContentItemResponse(ContentItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    verification_status: VerificationStatus
    approval_status: ApprovalStatus
    created_at: datetime
    updated_at: datetime
    source: Optional[SourceRecordResponse] = None


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_id: str
    asset_type: AssetType
    storage_url: str
    local_path: Optional[str] = None
    width: int
    height: int
    checksum: str
    created_at: datetime


class PublicationJobBase(BaseModel):
    content_id: str
    publication_type: PublicationType
    scheduled_at: datetime


class PublicationJobCreate(PublicationJobBase):
    pass


class PublicationAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    attempt_number: int
    request_started_at: datetime
    response_received_at: Optional[datetime] = None
    response_status: Optional[int] = None
    error_category: Optional[str] = None
    error_message_redacted: Optional[str] = None


class PublicationJobResponse(PublicationJobBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: str
    status: JobStatus
    attempt_count: int
    instagram_media_id: Optional[str] = None
    last_error: Optional[str] = None
    claimed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    content: Optional[ContentItemResponse] = None
    attempts: List[PublicationAttemptResponse] = []


class ExecutionSummary(BaseModel):
    date: str
    feed_posts_published: int = 0
    stories_published: int = 0
    notes_prepared: int = 0
    jobs_skipped: int = 0
    jobs_failed: int = 0
    details: List[str] = []
