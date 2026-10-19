"""
Content Library Management.
Provides CRUD, verification, approval gates, and querying for dhikr, dua, and Quranic content.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import (
    SourceRecord,
    ContentItem,
    SourceType,
    VerificationStatus,
    ApprovalStatus,
    ContentCategory,
    AuditLog,
)
from app.content.verification import validate_source, validate_content_item, compute_arabic_checksum


def add_source(
    db: Session,
    source_type: SourceType,
    source_name: str,
    reference: str,
    hadith_grade: Optional[str] = None,
    grading_source: Optional[str] = None,
    verification_notes: Optional[str] = None,
    verified_by: Optional[str] = None,
    auto_verify: bool = False,
) -> SourceRecord:
    """Adds a new source record to the library."""
    status = VerificationStatus.VERIFIED if auto_verify else VerificationStatus.UNVERIFIED
    verified_at = datetime.now(timezone.utc) if auto_verify else None

    source = SourceRecord(
        source_type=source_type,
        source_name=source_name.strip(),
        reference=reference.strip(),
        hadith_grade=hadith_grade.strip() if hadith_grade else None,
        grading_source=grading_source.strip() if grading_source else None,
        verification_notes=verification_notes,
        verified_by=verified_by,
        verified_at=verified_at,
        status=status,
    )

    db.add(source)
    db.flush()

    audit = AuditLog(
        action="SOURCE_CREATED",
        entity_type="source_record",
        entity_id=source.id,
        details=f"Source '{source.source_name}' ({source.reference}) added with status {status.value}"
    )
    db.add(audit)
    return source


def add_content_item(
    db: Session,
    category: ContentCategory,
    arabic_text: str,
    english_meaning: str,
    source_id: str,
    transliteration: Optional[str] = None,
    caption_ar: Optional[str] = None,
    caption_en: Optional[str] = None,
    is_demo: bool = False,
    auto_approve: bool = False,
) -> ContentItem:
    """Adds a new content item into the library."""
    item = ContentItem(
        category=category,
        arabic_text=arabic_text.strip(),
        english_meaning=english_meaning.strip(),
        source_id=source_id,
        transliteration=transliteration.strip() if transliteration else None,
        caption_ar=caption_ar.strip() if caption_ar else None,
        caption_en=caption_en.strip() if caption_en else None,
        is_demo=is_demo,
        verification_status=VerificationStatus.UNVERIFIED,
        approval_status=ApprovalStatus.APPROVED if auto_approve else ApprovalStatus.DRAFT,
    )
    db.add(item)
    db.flush()

    audit = AuditLog(
        action="CONTENT_CREATED",
        entity_type="content_item",
        entity_id=item.id,
        details=f"Content in category {category.value} added (is_demo={is_demo})"
    )
    db.add(audit)
    return item


def verify_content(
    db: Session,
    item_id: str,
    verified_by: str,
    notes: Optional[str] = None
) -> ContentItem:
    """
    Formally verifies a content item after checking its text and source.
    Raises ContentVerificationError if validation fails.
    """
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise ValueError(f"Content item {item_id} not found.")

    is_valid, errors = validate_content_item(item)
    if not is_valid:
        raise ValueError(f"Content failed verification rules: {'; '.join(errors)}")

    item.verification_status = VerificationStatus.VERIFIED
    item.updated_at = datetime.now(timezone.utc)

    # If source record is not yet marked verified, mark it
    if item.source and item.source.status != VerificationStatus.VERIFIED:
        item.source.status = VerificationStatus.VERIFIED
        item.source.verified_by = verified_by
        item.source.verified_at = datetime.now(timezone.utc)
        if notes:
            item.source.verification_notes = (item.source.verification_notes or "") + f"\n{notes}"

    audit = AuditLog(
        action="CONTENT_VERIFIED",
        entity_type="content_item",
        entity_id=item.id,
        details=f"Verified by {verified_by}. Notes: {notes or 'N/A'}"
    )
    db.add(audit)
    db.flush()
    return item


def approve_content(
    db: Session,
    item_id: str,
    approver: str
) -> ContentItem:
    """Approves a verified content item for scheduling and publishing."""
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise ValueError(f"Content item {item_id} not found.")

    if item.verification_status != VerificationStatus.VERIFIED:
        raise ValueError("Cannot approve content that has not been marked as VERIFIED.")

    item.approval_status = ApprovalStatus.APPROVED
    item.updated_at = datetime.now(timezone.utc)

    audit = AuditLog(
        action="CONTENT_APPROVED",
        entity_type="content_item",
        entity_id=item.id,
        details=f"Approved by {approver}"
    )
    db.add(audit)
    db.flush()
    return item


def list_approved_content(
    db: Session,
    category: Optional[ContentCategory] = None,
    exclude_demo: bool = True
) -> List[ContentItem]:
    """Retrieves all approved and verified content eligible for scheduling."""
    query = db.query(ContentItem).filter(
        ContentItem.approval_status == ApprovalStatus.APPROVED,
        ContentItem.verification_status == VerificationStatus.VERIFIED
    )
    if exclude_demo:
        query = query.filter(ContentItem.is_demo == False)  # noqa: E712
    if category:
        query = query.filter(ContentItem.category == category)
    return query.all()
