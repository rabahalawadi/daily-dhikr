"""
Direct Instagram Publisher using instagrapi.
Allows publishing to Instagram using username and password / session,
bypassing the Meta Developer App and Facebook Page requirements.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from app.config import settings

logger = logging.getLogger(__name__)


class InstagrapiPublisher:
    """Direct publisher utilizing instagrapi for username/password and session-based publishing."""

    def __init__(self):
        self._client = None
        self.username = settings.INSTAGRAM_USERNAME
        self.password = settings.INSTAGRAM_PASSWORD
        self.session_path = Path(settings.INSTAGRAM_SESSION_PATH)
        self.dry_run = settings.DRY_RUN
        self.publishing_enabled = settings.PUBLISHING_ENABLED

    def is_live_publishing_ready(self) -> Tuple[bool, Optional[str]]:
        """Checks whether credentials and safety switches allow live publishing."""
        if not self.publishing_enabled:
            return False, "Live publishing is disabled (PUBLISHING_ENABLED=False). Operating in safe dry-run mode."
        if self.dry_run:
            return False, "Operating in dry-run mode (DRY_RUN=True)."
        if not self.session_path.exists() and not settings.INSTAGRAM_SESSION_DATA:
            if not self.username or not self.password:
                return False, "Neither saved session nor INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD are configured."
        return True, None

    def get_client(self):
        """Initializes and authenticates the instagrapi Client."""
        if self._client is not None:
            return self._client

        from instagrapi import Client

        cl = Client()
        cl.delay_range = [2, 5]
        cl.login_flow = lambda: True

        # 1. Try loading from inline session data (GitHub Actions secret)
        if settings.INSTAGRAM_SESSION_DATA and settings.INSTAGRAM_SESSION_DATA.strip():
            try:
                session_dict = json.loads(settings.INSTAGRAM_SESSION_DATA)
                cl.set_settings(session_dict)
                logger.info("Loaded instagrapi session from INSTAGRAM_SESSION_DATA environment variable.")
            except Exception as e:
                logger.warning(f"Failed to load session from INSTAGRAM_SESSION_DATA: {e}")

        # 2. Try loading from session file
        elif self.session_path.exists():
            try:
                cl.load_settings(str(self.session_path))
                logger.info(f"Loaded instagrapi session from {self.session_path}")
            except Exception as e:
                logger.warning(f"Failed to load session from file: {e}")

        # 3. Check if session is authenticated
        logged_in = False
        try:
            if cl.user_id:
                # Quick verification check using account info rather than timeline feed
                cl.account_info()
                logged_in = True
                logger.info(f"Session valid for user_id: {cl.user_id}")
        except Exception:
            logged_in = False

        # 4. If not logged in, attempt fresh login with username/password
        if not logged_in:
            if not self.username or not self.password:
                raise ValueError("Instagram session invalid and INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD not provided.")

            logger.info(f"Logging in to Instagram as '{self.username}'...")
            try:
                cl.login(self.username, self.password)
            except Exception as err:
                if cl.user_id:
                    logger.info(f"Primary authentication succeeded (user_id: {cl.user_id}), ignoring notice: {err}")
                else:
                    raise err
            logger.info("Login successful. Saving session...")

            # Save session to file
            try:
                cl.dump_settings(str(self.session_path))
                logger.info(f"Session saved to {self.session_path}")
            except Exception as e:
                logger.warning(f"Could not save session file: {e}")

        self._client = cl
        return self._client

    def verify_account_access(self) -> Dict[str, Any]:
        """Validates login and retrieves profile information."""
        ready, reason = self.is_live_publishing_ready()
        if not ready:
            logger.info(f"[Dry Run / Safety] Skipping live instagrapi account verification: {reason}")
            return {
                "status": "simulated",
                "username": self.username or "dailydhikr_demo",
                "name": "Daily Dhikr Demo",
                "dry_run": True,
            }

        cl = self.get_client()
        user_info = cl.user_info(cl.user_id)
        return {
            "status": "authenticated",
            "id": str(user_info.pk),
            "username": user_info.username,
            "full_name": user_info.full_name,
            "is_private": user_info.is_private,
            "dry_run": False,
        }

    def publish_feed_post(self, image_path: str, caption: str) -> str:
        """Publishes a photo post to Instagram feed."""
        ready, reason = self.is_live_publishing_ready()
        if not ready:
            logger.info(f"[Dry Run] instagrapi.publish_feed_post({image_path}) - Caption len: {len(caption)}")
            return f"dryrun_instagrapi_feed_{int(time.time())}"

        cl = self.get_client()
        logger.info(f"Publishing feed post to Instagram via instagrapi: {image_path}")
        media = cl.photo_upload(path=Path(image_path), caption=caption)
        media_id = str(media.pk)
        logger.info(f"Published feed post successfully! Media PK: {media_id}")
        return media_id

    def publish_story(self, image_path: str) -> str:
        """Publishes a photo to Instagram Story."""
        ready, reason = self.is_live_publishing_ready()
        if not ready:
            logger.info(f"[Dry Run] instagrapi.publish_story({image_path})")
            return f"dryrun_instagrapi_story_{int(time.time())}"

        cl = self.get_client()
        logger.info(f"Publishing story to Instagram via instagrapi: {image_path}")
        media = cl.photo_upload_to_story(path=Path(image_path))
        media_id = str(media.pk)
        logger.info(f"Published story successfully! Media PK: {media_id}")
        return media_id


instagrapi_publisher = InstagrapiPublisher()
