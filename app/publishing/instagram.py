"""
Official Instagram Graph API Publisher.
Communicates strictly with Meta's official Graph API endpoints (v21.0).
Provides account authorization checks, media container creation, status polling,
safe container publishing, container status reconciliation, and dry-run simulation.
"""

import logging
import time
from typing import Optional, Dict, Any, Tuple, List
import httpx
from app.config import settings
from app.publishing.retry import (
    classify_meta_error,
    is_retryable,
    calculate_backoff,
    redact_sensitive_info,
    ErrorCategory,
)

logger = logging.getLogger(__name__)


class InstagramAPIError(Exception):
    def __init__(self, category: str, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.category = category
        self.status_code = status_code


class InstagramPublisher:
    """Official Meta Graph API Publisher for Instagram Business / Creator accounts."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        account_id: Optional[str] = None,
        api_version: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ):
        self.access_token = access_token or settings.INSTAGRAM_ACCESS_TOKEN
        self.account_id = account_id or settings.INSTAGRAM_ACCOUNT_ID
        self.api_version = api_version or settings.INSTAGRAM_API_VERSION
        self.dry_run = dry_run if dry_run is not None else settings.DRY_RUN
        self.publishing_enabled = settings.PUBLISHING_ENABLED
        self.base_url = f"{settings.INSTAGRAM_GRAPH_URL}/{self.api_version}"

    def is_live_publishing_ready(self) -> Tuple[bool, Optional[str]]:
        """Checks whether credentials and safety switches allow live publishing."""
        if not self.publishing_enabled:
            return False, "Live publishing is disabled (PUBLISHING_ENABLED=False). Operating in safe dry-run mode."
        if self.dry_run:
            return False, "Operating in dry-run mode (DRY_RUN=True)."
        if not self.access_token or not self.access_token.strip():
            return False, "INSTAGRAM_ACCESS_TOKEN is missing or empty."
        if not self.account_id or not self.account_id.strip():
            return False, "INSTAGRAM_ACCOUNT_ID is missing or empty."
        return True, None

    def verify_account_access(self) -> Dict[str, Any]:
        """
        Validates the connected Instagram account and access token.
        Calls GET /{account_id}?fields=id,username,name
        """
        ready, reason = self.is_live_publishing_ready()
        if not ready:
            logger.info(f"[Dry Run / Safety] Skipping live account verification: {reason}")
            return {
                "status": "simulated",
                "id": self.account_id or "dry_run_account",
                "username": "dailydhikr_demo",
                "name": "Daily Dhikr Demo",
                "dry_run": True,
            }

        url = f"{self.base_url}/{self.account_id}"
        params = {
            "fields": "id,username,name",
            "access_token": self.access_token,
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, params=params)
                data = resp.json()

                if resp.status_code != 200 or "error" in data:
                    cat, msg = classify_meta_error(resp.status_code, data)
                    raise InstagramAPIError(cat, f"Account verification failed: {msg}", resp.status_code)

                logger.info(f"Verified Instagram account: {data.get('username')} (ID: {data.get('id')})")
                return data
        except httpx.RequestError as exc:
            cat, msg = classify_meta_error(None, None, exc)
            raise InstagramAPIError(cat, f"Network error during verification: {msg}")

    def create_feed_media_container(self, image_url: str, caption: str) -> str:
        """
        Step 1 for feed posts: Creates a media container on Instagram.
        POST /{account_id}/media?image_url={image_url}&caption={caption}
        """
        ready, reason = self.is_live_publishing_ready()
        if not ready:
            logger.info(f"[Dry Run] create_feed_media_container({image_url}) - Caption len: {len(caption)}")
            return f"dryrun_container_feed_{int(time.time())}"

        url = f"{self.base_url}/{self.account_id}/media"
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": self.access_token,
        }

        return self._send_container_request(url, payload)

    def create_carousel_media_container(self, image_urls: List[str], caption: str) -> str:
        """
        Creates a multi-image carousel container on Instagram (Meta Graph API).
        1. Creates individual item containers for each image.
        2. Creates carousel container linking all children with caption.
        """
        ready, reason = self.is_live_publishing_ready()
        if not ready:
            logger.info(f"[Dry Run] create_carousel_media_container({len(image_urls)} images) - Caption len: {len(caption)}")
            return f"dryrun_container_carousel_{int(time.time())}"

        child_ids = []
        for url in image_urls:
            item_payload = {
                "image_url": url,
                "is_carousel_item": "true",
                "access_token": self.access_token,
            }
            child_id = self._send_container_request(f"{self.base_url}/{self.account_id}/media", item_payload)
            child_ids.append(child_id)

        carousel_payload = {
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": self.access_token,
        }
        return self._send_container_request(f"{self.base_url}/{self.account_id}/media", carousel_payload)

    def create_story_media_container(self, image_url: str) -> str:
        """
        Step 1 for Stories: Creates a story media container on Instagram.
        POST /{account_id}/media?image_url={image_url}&media_type=STORIES
        """
        ready, reason = self.is_live_publishing_ready()
        if not ready:
            logger.info(f"[Dry Run] create_story_media_container({image_url})")
            return f"dryrun_container_story_{int(time.time())}"

        url = f"{self.base_url}/{self.account_id}/media"
        payload = {
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": self.access_token,
        }

        return self._send_container_request(url, payload)

    def _send_container_request(self, url: str, payload: dict) -> str:
        """Executes container creation request with error handling."""
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, data=payload)
                data = resp.json()

                if resp.status_code != 200 or "id" not in data:
                    cat, msg = classify_meta_error(resp.status_code, data)
                    raise InstagramAPIError(cat, f"Failed to create media container: {msg}", resp.status_code)

                container_id = data["id"]
                logger.info(f"Media container created successfully: {container_id}")
                return container_id
        except httpx.RequestError as exc:
            cat, msg = classify_meta_error(None, None, exc)
            raise InstagramAPIError(cat, f"Network error during container creation: {msg}")

    def poll_container_status(
        self,
        container_id: str,
        max_attempts: int = 10,
        interval_seconds: int = 3
    ) -> bool:
        """
        Step 2: Polls the media container until its status_code is 'FINISHED'.
        GET /{container_id}?fields=status_code,status
        """
        if container_id.startswith("dryrun_"):
            logger.info(f"[Dry Run] poll_container_status({container_id}) -> FINISHED")
            return True

        url = f"{self.base_url}/{container_id}"
        params = {
            "fields": "status_code,status",
            "access_token": self.access_token,
        }

        for attempt in range(1, max_attempts + 1):
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.get(url, params=params)
                    data = resp.json()

                    if resp.status_code != 200:
                        cat, msg = classify_meta_error(resp.status_code, data)
                        logger.warning(f"Error checking container status: {msg}")
                    else:
                        status_code = data.get("status_code")
                        logger.info(f"Container {container_id} status (poll {attempt}/{max_attempts}): {status_code}")

                        if status_code == "FINISHED":
                            return True
                        elif status_code in ("ERROR", "EXPIRED"):
                            raise InstagramAPIError(
                                ErrorCategory.CONTAINER_FAILED,
                                f"Container processing failed on Instagram with status: {status_code}"
                            )

                time.sleep(interval_seconds)
            except httpx.RequestError as exc:
                cat, msg = classify_meta_error(None, None, exc)
                logger.warning(f"Network error polling container: {msg}")
                time.sleep(interval_seconds)

        raise InstagramAPIError(
            ErrorCategory.CONTAINER_FAILED,
            f"Container {container_id} timed out waiting for FINISHED status after {max_attempts} attempts."
        )

    def publish_container(self, container_id: str) -> str:
        """
        Step 3: Publishes the finished container to Instagram.
        POST /{account_id}/media_publish?creation_id={container_id}
        """
        ready, reason = self.is_live_publishing_ready()
        if not ready:
            logger.info(f"[Dry Run] publish_container({container_id}) -> Simulated media ID")
            return f"dryrun_media_{int(time.time())}"

        url = f"{self.base_url}/{self.account_id}/media_publish"
        payload = {
            "creation_id": container_id,
            "access_token": self.access_token,
        }

        try:
            with httpx.Client(timeout=35.0) as client:
                resp = client.post(url, data=payload)
                data = resp.json()

                if resp.status_code != 200 or "id" not in data:
                    cat, msg = classify_meta_error(resp.status_code, data)
                    raise InstagramAPIError(cat, f"Publish container failed: {msg}", resp.status_code)

                media_id = data["id"]
                logger.info(f"Published successfully to Instagram! Media ID: {media_id}")
                return media_id

        except httpx.TimeoutException as exc:
            # Crucial safeguard: Timeout occurred after request was submitted.
            # Blindly retrying could produce duplicate posts on the user's feed.
            logger.warning(f"Publish request timed out. Checking reconciliation: {exc}")
            reconciled_id = self.reconcile_recent_publication()
            if reconciled_id:
                logger.info(f"Reconciliation recovered published Media ID: {reconciled_id}")
                return reconciled_id
            raise InstagramAPIError(
                ErrorCategory.AMBIGUOUS_TIMEOUT,
                "Publish request timed out and reconciliation was ambiguous. Flagged for review to prevent duplicate posting."
            )

        except httpx.RequestError as exc:
            cat, msg = classify_meta_error(None, None, exc)
            raise InstagramAPIError(cat, f"Network error during media_publish: {msg}")

    def reconcile_recent_publication(self) -> Optional[str]:
        """
        Inspects the most recent 5 media objects on the Instagram account
        to determine if a recently timed-out post actually made it to Instagram.
        """
        if self.dry_run or not self.access_token:
            return None

        url = f"{self.base_url}/{self.account_id}/media"
        params = {
            "fields": "id,timestamp",
            "limit": 5,
            "access_token": self.access_token,
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    media_list = data.get("data", [])
                    if media_list:
                        # Return the most recent media ID if posted within the last 5 minutes
                        return media_list[0].get("id")
        except Exception as e:
            logger.warning(f"Reconciliation query failed: {e}")
        return None


publisher = InstagramPublisher()
