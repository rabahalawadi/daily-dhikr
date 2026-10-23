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

    @property
    def resolved_database_url(self) -> str:
        """Resolves relative SQLite URL to absolute path rooted at PROJECT_ROOT."""
        if self.DATABASE_URL in ("sqlite:///./daily_dhikr.db", "sqlite:///daily_dhikr.db"):
            db_file = self.PROJECT_ROOT / "daily_dhikr.db"
            return f"sqlite:///{db_file.as_posix()}"
        return self.DATABASE_URL

    # Timezone
    TIMEZONE: str = Field(
        default="Asia/Amman",
        description="Target timezone name (e.g. Asia/Amman). Never hardcoded as a fixed offset."
    )

    # Scheduling Mode & Prayer Times Configuration
    SCHEDULE_MODE: str = Field(
        default="prayer_times",
        description="Scheduling mode: 'prayer_times' (aligned with Fajr, Duha, Dhuhr, Asr, Isha) or 'fixed_slots'"
    )
    PRAYER_CITY: str = Field(
        default="Amman",
        description="City for Islamic prayer times calculation."
    )
    PRAYER_COUNTRY: str = Field(
        default="Jordan",
        description="Country for Islamic prayer times calculation."
    )
    PRAYER_LATITUDE: float = Field(
        default=31.9539,
        description="Geographic latitude for astronomical prayer calculation."
    )
    PRAYER_LONGITUDE: float = Field(
        default=35.9106,
        description="Geographic longitude for astronomical prayer calculation."
    )
    PRAYER_METHOD: int = Field(
        default=4,
        description="Calculation method: 4=Umm Al-Qura, 5=Egyptian General Authority, 3=Muslim World League."
    )
    FAJR_OFFSET_MINUTES: int = Field(
        default=0,
        description="Offset in minutes relative to Fajr prayer (e.g. 0 for adhan time, +10 for after prayer)."
    )
    DUHA_OFFSET_MINUTES_AFTER_SUNRISE: int = Field(
        default=90,
        description="Minutes after sunrise to publish daily feed reminder (Duha prayer time)."
    )
    DHUHR_OFFSET_MINUTES: int = Field(
        default=0,
        description="Offset in minutes relative to Dhuhr prayer."
    )
    ASR_OFFSET_MINUTES: int = Field(
        default=0,
        description="Offset in minutes relative to Asr prayer (start of Evening Adhkar)."
    )
    ISHA_OFFSET_MINUTES: int = Field(
        default=0,
        description="Offset in minutes relative to Isha prayer."
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

    # Direct Instagram Login Credentials (instagrapi)
    PUBLISHER_TYPE: str = Field(
        default="instagrapi",
        description="Publishing backend: 'instagrapi' (direct login) or 'official' (Meta Graph API)"
    )
    INSTAGRAM_USERNAME: Optional[str] = Field(
        default=None,
        description="Instagram username or email."
    )
    INSTAGRAM_PASSWORD: Optional[str] = Field(
        default=None,
        description="Instagram account password."
    )
    INSTAGRAM_SESSION_PATH: str = Field(
        default="session.json",
        description="File path to store or load the serialized instagrapi session."
    )
    INSTAGRAM_SESSION_DATA: Optional[str] = Field(
        default=None,
        description="Serialized session JSON string (useful for GitHub Secrets)."
    )

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

    # Typography Settings
    ARABIC_FONT_NAME: str = Field(
        default="cairo",
        description="Arabic typography choice: 'cairo' (brand modern typography), 'noto_sans' (clean sans-serif), or 'amiri' (calligraphy)."
    )
    STRIP_TASHKEEL_ON_IMAGES: bool = Field(
        default=False,
        description="Preserves full Tashkeel (diacritical marks) on graphic renders using OpenType GPOS positioning."
    )

    def get_arabic_font_path(self) -> Path:
        """Returns path to the selected verified Arabic font."""
        if self.ARABIC_FONT_NAME == "cairo":
            cairo = self.FONTS_DIR / "Cairo.ttf"
            if cairo.exists():
                return cairo

        if self.ARABIC_FONT_NAME == "noto_sans":
            noto = self.FONTS_DIR / "NotoSansArabic.ttf"
            if noto.exists():
                return noto

        if self.ARABIC_FONT_NAME == "amiri":
            amiri_bold = self.FONTS_DIR / "Amiri-Bold.ttf"
            if amiri_bold.exists():
                return amiri_bold
            amiri_reg = self.FONTS_DIR / "Amiri-Regular.ttf"
            if amiri_reg.exists():
                return amiri_reg

        # Fallback order
        for name in ("Cairo.ttf", "NotoSansArabic.ttf", "Amiri-Bold.ttf"):
            p = self.FONTS_DIR / name
            if p.exists():
                return p
        return self.FONTS_DIR / "Cairo.ttf"

    def get_uthmanic_font_path(self) -> Path:
        """Returns path to the verified King Fahd Complex Uthmanic Quran script font."""
        for name in ("UthmanicHafs.otf", "UthmanicHafs.ttf", "Amiri-Bold.ttf"):
            p = self.FONTS_DIR / name
            if p.exists():
                return p
        return self.get_arabic_font_path()

    def get_cairo_font_path(self) -> Path:
        """Returns path to Cairo font (used for Hadith, Adhkar, and general text)."""
        cairo = self.FONTS_DIR / "Cairo.ttf"
        if cairo.exists():
            return cairo
        return self.get_arabic_font_path()

    def get_inter_font_path(self) -> Path:
        """Returns path to Inter English font."""
        primary = self.FONTS_DIR / "Inter.ttf"
        if primary.exists():
            return primary
        fallback = self.FONTS_DIR / "Inter-Regular.ttf"
        return fallback if fallback.exists() else primary


# Singleton settings instance
settings = Settings()
