"""
Unit tests for InstagrapiPublisher backend.
"""

from unittest.mock import MagicMock, patch
from pathlib import Path
from app.config import settings
from app.publishing.instagrapi_client import InstagrapiPublisher


def test_instagrapi_dry_run_mode(monkeypatch):
    monkeypatch.setattr(settings, "DRY_RUN", True)
    monkeypatch.setattr(settings, "PUBLISHING_ENABLED", False)

    pub = InstagrapiPublisher()
    ready, reason = pub.is_live_publishing_ready()
    assert ready is False
    assert "Operating in safe dry-run mode" in reason

    feed_res = pub.publish_feed_post("dummy.jpg", "Test Caption")
    assert feed_res.startswith("dryrun_instagrapi_feed_")

    story_res = pub.publish_story("dummy.jpg")
    assert story_res.startswith("dryrun_instagrapi_story_")

    acct = pub.verify_account_access()
    assert acct["dry_run"] is True
    assert acct["status"] == "simulated"


def test_instagrapi_live_publishing_mock(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DRY_RUN", False)
    monkeypatch.setattr(settings, "PUBLISHING_ENABLED", True)
    monkeypatch.setattr(settings, "INSTAGRAM_USERNAME", "testuser")
    monkeypatch.setattr(settings, "INSTAGRAM_PASSWORD", "testpass")
    session_file = tmp_path / "test_session.json"
    monkeypatch.setattr(settings, "INSTAGRAM_SESSION_PATH", str(session_file))

    pub = InstagrapiPublisher()
    mock_cl = MagicMock()
    mock_cl.user_id = "12345678"
    mock_media = MagicMock()
    mock_media.pk = "9988776655"
    mock_cl.photo_upload.return_value = mock_media
    mock_cl.photo_upload_to_story.return_value = mock_media

    pub._client = mock_cl

    # Test feed publish
    media_id = pub.publish_feed_post("test.jpg", "Caption")
    assert media_id == "9988776655"
    mock_cl.photo_upload.assert_called_once()

    # Test story publish
    story_id = pub.publish_story("test.jpg")
    assert story_id == "9988776655"
    mock_cl.photo_upload_to_story.assert_called_once()
