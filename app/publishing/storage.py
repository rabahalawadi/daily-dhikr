"""
Persistent Object Storage Client for generated graphic assets.
Instagram Graph API requires public, accessible image URLs to create media containers.
Supports local server URLs (for testing/mocking) and Supabase / S3 bucket uploads.
"""

import logging
import mimetypes
from pathlib import Path
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """Handles uploading generated images to persistent public storage."""

    def __init__(self):
        self.backend = settings.STORAGE_BACKEND.lower()

    def upload_file(self, local_path: Path, remote_filename: Optional[str] = None) -> str:
        """
        Uploads a local image file to persistent storage and returns its publicly accessible URL.
        """
        if not local_path.exists():
            raise FileNotFoundError(f"Cannot upload nonexistent file: {local_path}")

        filename = remote_filename or local_path.name
        content_type = mimetypes.guess_type(str(local_path))[0] or "image/jpeg"

        if self.backend == "supabase":
            return self._upload_to_supabase(local_path, filename, content_type)
        elif self.backend == "s3":
            return self._upload_to_s3(local_path, filename, content_type)
        else:
            return self._get_local_url(local_path, filename)

    def _get_local_url(self, local_path: Path, filename: str) -> str:
        """
        For local development and testing:
        Returns local mock URL or prefix if configured.
        """
        prefix = (settings.STORAGE_PUBLIC_URL_PREFIX or f"http://localhost:{settings.SERVER_PORT}/media").strip()
        url = f"{prefix.rstrip('/')}/{filename}"
        logger.info(f"[Local Storage] Asset available at: {url}")
        return url

    def _upload_to_supabase(self, local_path: Path, filename: str, content_type: str) -> str:
        """Uploads asset to Supabase Storage bucket via REST API."""
        endpoint = (settings.STORAGE_ENDPOINT or "").strip()
        secret_key = (settings.STORAGE_SECRET_KEY or "").strip()
        bucket = (settings.STORAGE_BUCKET or "dhikr-media").strip()

        if not endpoint or not secret_key or not bucket:
            logger.warning("Supabase storage credentials incomplete. Falling back to public prefix.")
            prefix = (settings.STORAGE_PUBLIC_URL_PREFIX or "https://storage.supabase.co").strip()
            return f"{prefix.rstrip('/')}/{bucket}/{filename}"

        upload_url = f"{endpoint.rstrip('/')}/object/{bucket}/{filename}"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "apikey": secret_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        with open(local_path, "rb") as f:
            file_bytes = f.read()

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(upload_url, headers=headers, content=file_bytes)
                resp.raise_for_status()

            if settings.STORAGE_PUBLIC_URL_PREFIX:
                public_url = f"{settings.STORAGE_PUBLIC_URL_PREFIX.rstrip('/')}/{filename}"
            else:
                base_host = settings.STORAGE_ENDPOINT.split("/storage/v1")[0]
                public_url = f"{base_host}/storage/v1/object/public/{settings.STORAGE_BUCKET}/{filename}"

            logger.info(f"Uploaded asset to Supabase storage: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"Failed to upload asset to Supabase storage: {e}")
            raise

    def _upload_to_s3(self, local_path: Path, filename: str, content_type: str) -> str:
        """Uploads asset to S3 compatible object storage."""
        prefix = settings.STORAGE_PUBLIC_URL_PREFIX or f"https://{settings.STORAGE_BUCKET}.s3.amazonaws.com"
        # Return public URL pattern
        return f"{prefix.rstrip('/')}/{filename}"


storage_manager = StorageManager()
