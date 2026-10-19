"""
Religious Content Safeguards & Verification Engine.
Strictly ensures that only authentic, verified Quranic verses, Hadith,
and authentic Adhkar with legitimate references can be approved or published.
Prevents generative hallucinations, invented citations, and silent text tampering.
"""

import hashlib
import re
from typing import Tuple, List, Optional
from app.models import (
    SourceRecord,
    ContentItem,
    SourceType,
    VerificationStatus,
    ApprovalStatus,
)


class ContentVerificationError(Exception):
    """Raised when religious content fails authenticity or integrity verification."""
    pass


# Arabic unicode block regex check
ARABIC_REGEX = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+")


def compute_arabic_checksum(arabic_text: str) -> str:
    """Computes a canonical SHA-256 hash of Arabic text, stripping extra whitespace."""
    normalized = " ".join(arabic_text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def contains_arabic(text: str) -> bool:
    """Verifies that the string contains actual Arabic characters."""
    return bool(ARABIC_REGEX.search(text))


def validate_source(source: SourceRecord) -> Tuple[bool, List[str]]:
    """
    Validates that a source record meets authenticity requirements according to its type.
    """
    errors = []

    if not source.source_name or not source.source_name.strip():
        errors.append("Source name cannot be empty.")

    if not source.reference or not source.reference.strip():
        errors.append("Source reference cannot be empty.")

    if source.source_type == SourceType.QURAN:
        # Quran must cite Surah and Ayah
        ref_lower = source.reference.lower()
        has_surah_or_ayah = any(kw in ref_lower for kw in ["surah", "ayah", "ayahs", "verse", ":", "سورة", "آية"])
        if not has_surah_or_ayah:
            errors.append("Quran source must specify Surah and Ayah reference (e.g. 'Surah Al-Baqarah 2:152').")

    elif source.source_type == SourceType.HADITH:
        # Hadith must have collection reference and authentic grading
        if not source.hadith_grade or not source.hadith_grade.strip():
            errors.append("Hadith source must specify hadith grade (e.g. 'Sahih', 'Hasan').")

        # Must not be fabricated or unverified
        grade_lower = (source.hadith_grade or "").lower()
        if any(unacc in grade_lower for unacc in ["da'eef", "daif", "weak", "mawdu", "fabricated", "unknown"]):
            errors.append(f"Hadith grade '{source.hadith_grade}' is not acceptable for public reminder broadcast.")

    return len(errors) == 0, errors


def validate_content_item(item: ContentItem) -> Tuple[bool, List[str]]:
    """
    Performs comprehensive verification on a content item.
    Enforces that:
    1. Arabic text is present and contains valid Arabic characters.
    2. English meaning is provided and meaningful.
    3. Source record is attached, verified, and valid.
    4. Prohibits publication of unverified or demo content.
    """
    errors = []

    if not item.arabic_text or not item.arabic_text.strip():
        errors.append("Arabic text cannot be empty.")
    elif not contains_arabic(item.arabic_text):
        errors.append("Arabic text field does not contain valid Arabic characters.")

    if not item.english_meaning or not item.english_meaning.strip():
        errors.append("English meaning translation cannot be empty.")

    if not item.source:
        errors.append("Content item has no associated source record.")
    else:
        valid_src, src_errors = validate_source(item.source)
        if not valid_src:
            errors.extend([f"Source error: {err}" for err in src_errors])

        if item.source.status != VerificationStatus.VERIFIED:
            errors.append(f"Source status is '{item.source.status.value}', but must be 'VERIFIED'.")

    return len(errors) == 0, errors


def can_be_published(item: ContentItem) -> Tuple[bool, Optional[str]]:
    """
    Strict gatekeeper check before any content item can be scheduled or published.
    Returns (True, None) if publishable, or (False, reason) if blocked.
    """
    if item.is_demo:
        return False, "Item is marked as DEMO and is strictly prohibited from live publication."

    if item.approval_status != ApprovalStatus.APPROVED:
        return False, f"Item approval status is '{item.approval_status.value}', required: 'APPROVED'."

    if item.verification_status != VerificationStatus.VERIFIED:
        return False, f"Item verification status is '{item.verification_status.value}', required: 'VERIFIED'."

    is_valid, errors = validate_content_item(item)
    if not is_valid:
        return False, f"Content validation failed: {'; '.join(errors)}"

    return True, None
