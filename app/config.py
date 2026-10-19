"""
Configuration management for Daily Dhikr Automation.
Loads configuration from environment variables or .env file with safe defaults.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base Paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    ASSETS_DIR: Path = PROJECT_ROOT / "assets"
    FONTS_DIR: Path = ASSETS_DIR / "fonts"
    OUTPUT_MEDIA_DIR: Path = PROJECT_ROOT / "generated_assets"

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./daily_dhikr.db",
        description="PostgreSQL URL for production (e.g. Supabase) or SQLite for local dev/testing"
    )

    # Timezone
    TIMEZONE: str = Field(
        default="Asia/Amman",
        description="Target timezone name (e.g. Asia/Amman). Never hardcoded as a fixed offset."
    )

    # Safety & Publishing Controls
    DRY_RUN: bool = Field(
        default=True,
        description="Default True. In dry-run mode, all validation and rendering runs without calling Instagram API."
    )
    PUBLISHING_ENABLED: bool = Field(
        default=False,
        description="Global kill switch. Must be explicitly set to True to send real publish requests."
    )

    # Official Instagram Graph API Credentials
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = Field(
        default=None,
        description="Meta User/Page Access Token with required permissions."
    )
    INSTAGRAM_ACCOUNT_ID: Optional[str] = Field(
        default=None,
        description="Connected Instagram Business/Creator Account ID."
    )
    INSTAGRAM_API_VERSION: str = Field(
        default="v21.0",
        description="Meta Graph API version."
    )
    INSTAGRAM_GRAPH_URL: str = "https://graph.facebook.com"

    # Persistent Object Storage (Required by Instagram Container Creation)
    STORAGE_BACKEND: str = Field(
        default="local",
        description="Object storage backend: 'local', 'supabase', or 's3'"
    )
    STORAGE_ENDPOINT: Optional[str] = None
    STORAGE_BUCKET: Optional[str] = "dhikr-media"
    STORAGE_ACCESS_KEY: Optional[str] = None
    STORAGE_SECRET_KEY: Optional[str] = None
    STORAGE_PUBLIC_URL_PREFIX: Optional[str] = None

    # Notifications
    NOTIFICATION_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="Webhook URL (Discord, Slack, Telegram, or generic JSON endpoint) for alerts."
    )
    NOTIFICATION_EMAIL_ENABLED: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    NOTIFICATION_EMAIL_RECIPIENT: Optional[str] = None

    # Retry and Scheduler Settings
    MAX_RETRY_ATTEMPTS: int = 3
    BASE_RETRY_DELAY_SECONDS: int = 5
    CATCH_UP_WINDOW_HOURS: int = 24  # Grace period for delayed scheduled jobs

    # Admin Dashboard API
    ADMIN_API_KEY: Optional[str] = None
    SERVER_PORT: int = 8000
    SERVER_HOST: str = "0.0.0.0"

    # Brand Colors
    COLOR_FOREST_GREEN: str = "#244936"
    COLOR_SAGE_GREEN: str = "#E7EEE5"
    COLOR_CREAM: str = "#FAF8F1"
    COLOR_GOLD: str = "#B99A59"

    def get_cairo_font_path(self) -> Path:
        """Returns path to Cairo Arabic font."""
        primary = self.FONTS_DIR / "Cairo.ttf"
        if primary.exists():
            return primary
        fallback = self.FONTS_DIR / "Cairo-Regular.ttf"
        return fallback if fallback.exists() else primary

    def get_inter_font_path(self) -> Path:
        """Returns path to Inter English font."""
        primary = self.FONTS_DIR / "Inter.ttf"
        if primary.exists():
            return primary
        fallback = self.FONTS_DIR / "Inter-Regular.ttf"
        return fallback if fallback.exists() else primary


# Singleton settings instance
settings = Settings()
