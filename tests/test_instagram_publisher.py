"""
Tests for official Instagram Graph API publisher, mocked responses, and dry-run safety.
Unit tests never make real HTTP calls to Meta's endpoints.
"""

import pytest
from app.publishing.instagram import InstagramPublisher, InstagramAPIError
from app.publishing.retry import redact_sensitive_info, classify_meta_error, ErrorCategory


def test_dry_run_mode_does_not_call_external_api():
    """In dry-run mode, publisher returns simulated container and media IDs safely."""
    pub = InstagramPublisher(dry_run=True)
    assert pub.is_live_publishing_ready()[0] is False

    container_id = pub.create_feed_media_container(
        image_url="http://test.local/img.jpg",
        caption="Sample Caption"
    )
    assert container_id.startswith("dryrun_container_")

    is_finished = pub.poll_container_status(container_id)
    assert is_finished is True

    media_id = pub.publish_container(container_id)
    assert media_id.startswith("dryrun_media_")


def test_token_redaction_in_logs_and_errors():
    """Ensures sensitive access tokens are completely redacted."""
    raw_message = "Error in https://graph.facebook.com/v21.0/123/media?access_token=EAABwzL90xyz123&caption=test"
    redacted = redact_sensitive_info(raw_message)

    assert "EAABwzL90xyz123" not in redacted
    assert "access_token=[REDACTED]" in redacted


def test_meta_error_classification():
    """Verifies that Meta API error codes are correctly mapped to error categories."""
    # Code 190 -> AUTHENTICATION_EXPIRED
    err_190 = {"error": {"code": 190, "message": "Error validating access token: Session has expired."}}
    cat, msg = classify_meta_error(400, err_190)
    assert cat == ErrorCategory.AUTHENTICATION_EXPIRED

    # Code 4 -> RATE_LIMITED
    err_rate = {"error": {"code": 4, "message": "Application request limit reached."}}
    cat, msg = classify_meta_error(400, err_rate)
    assert cat == ErrorCategory.RATE_LIMITED

    # Code 10 -> PERMISSION_DENIED
    err_perm = {"error": {"code": 10, "message": "Application does not have permission."}}
    cat, msg = classify_meta_error(403, err_perm)
    assert cat == ErrorCategory.PERMISSION_DENIED
