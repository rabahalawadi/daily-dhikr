"""
Timezone calculations and scheduling slots for Daily Dhikr.
Explicitly uses IANA zone names (defaulting to Asia/Amman) via zoneinfo.
Never relies on a permanently hardcoded offset.
"""

from datetime import datetime, date, time as dtime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import logging
from typing import Dict, List, Optional
from app.config import settings
from app.models import PublicationType, ContentCategory

logger = logging.getLogger(__name__)


def get_configured_timezone():
    """Returns the ZoneInfo instance for the configured timezone or fallback."""
    try:
        return ZoneInfo(settings.TIMEZONE)
    except (ZoneInfoNotFoundError, Exception) as e:
        logger.warning(f"ZoneInfo('{settings.TIMEZONE}') failed: {e}. Falling back to UTC+3.")
        return timezone(timedelta(hours=3))


def get_current_local_time(tz_name: Optional[str] = None) -> datetime:
    """Returns the current timezone-aware datetime in the configured timezone."""
    tz = ZoneInfo(tz_name) if tz_name else get_configured_timezone()
    return datetime.now(tz)


def to_utc(dt: datetime) -> datetime:
    """Ensures a datetime is timezone-aware and converted to UTC."""
    if dt.tzinfo is None:
        # Treat naive datetime as in configured timezone
        dt = dt.replace(tzinfo=get_configured_timezone())
    return dt.astimezone(timezone.utc)


def to_local(dt: datetime, tz_name: Optional[str] = None) -> datetime:
    """Converts a UTC or naive datetime to the local configured timezone."""
    tz = ZoneInfo(tz_name) if tz_name else get_configured_timezone()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


# Standard Jordan time daily content schedule
DAILY_SLOTS_JORDAN_TIME = [
    {
        "slot_name": "morning_story",
        "time_str": "07:00",
        "pub_type": PublicationType.STORY_POST,
        "category": ContentCategory.MORNING_DHIKR,
        "template": "morning_story",
    },
    {
        "slot_name": "feed_post",
        "time_str": "09:00",
        "pub_type": PublicationType.FEED_POST,
        "category": ContentCategory.VERSE_OF_THE_DAY,
        "template": "verse_of_the_day",
    },
    {
        "slot_name": "reminder_story",
        "time_str": "12:00",
        "pub_type": PublicationType.STORY_POST,
        "category": ContentCategory.DUA,
        "template": "dua_story",
    },
    {
        "slot_name": "evening_story",
        "time_str": "17:00",
        "pub_type": PublicationType.STORY_POST,
        "category": ContentCategory.EVENING_DHIKR,
        "template": "evening_story",
    },
    {
        "slot_name": "daily_note",
        "time_str": "20:00",
        "pub_type": PublicationType.NOTE,
        "category": ContentCategory.NOTE,
        "template": None,
    },
]


def calculate_slot_datetimes(target_date: Optional[date] = None) -> List[Dict]:
    """
    Computes local and UTC datetimes for all daily slots on the target date.
    When settings.SCHEDULE_MODE is 'prayer_times' (default), aligns slots dynamically
    with Islamic prayer times (Fajr, Duha, Dhuhr, Asr, Isha).
    Otherwise, uses fixed standard Jordan time slots.
    On Fridays (Jumu'ah), adapts the feed post to 06:00 AM FRIDAY_SPECIAL (Surat Al-Kahf).
    """
    tz = get_configured_timezone()
    today = target_date or get_current_local_time().date()
    is_friday = today.weekday() == 4

    if getattr(settings, "SCHEDULE_MODE", "prayer_times") == "prayer_times":
        try:
            from app.scheduler.prayer_times import get_prayer_schedule_slots
            return get_prayer_schedule_slots(
                target_date=today,
                tz=tz,
                city=settings.PRAYER_CITY,
                country=settings.PRAYER_COUNTRY,
                lat=settings.PRAYER_LATITUDE,
                lon=settings.PRAYER_LONGITUDE,
                method=settings.PRAYER_METHOD,
                fajr_offset=settings.FAJR_OFFSET_MINUTES,
                duha_offset_after_sunrise=settings.DUHA_OFFSET_MINUTES_AFTER_SUNRISE,
                dhuhr_offset=settings.DHUHR_OFFSET_MINUTES,
                asr_offset=settings.ASR_OFFSET_MINUTES,
                isha_offset=settings.ISHA_OFFSET_MINUTES,
            )
        except Exception as e:
            logger.warning(f"Error computing prayer times schedule: {e}. Falling back to fixed slots.")

    slots = []
    for slot_def in DAILY_SLOTS_JORDAN_TIME:
        slot = dict(slot_def)
        if slot["slot_name"] == "feed_post":
            if is_friday:
                slot["time_str"] = "06:00"
                slot["category"] = ContentCategory.FRIDAY_SPECIAL
                slot["template"] = "surah_kahf_carousel"
            else:
                slot["time_str"] = "09:00"
                slot["category"] = ContentCategory.VERSE_OF_THE_DAY
                slot["template"] = "verse_of_the_day"

        hour, minute = map(int, slot["time_str"].split(":"))
        local_dt = datetime.combine(today, dtime(hour=hour, minute=minute), tzinfo=tz)
        utc_dt = local_dt.astimezone(timezone.utc)

        slots.append({
            **slot,
            "scheduled_local": local_dt,
            "scheduled_utc": utc_dt,
        })

    return slots
