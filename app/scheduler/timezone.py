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
        "category": ContentCategory.DAILY_REMINDER,
        "template": "feed_post",
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
    Correctly accounts for daylight-saving rules via zoneinfo.
    """
    tz = get_configured_timezone()
    today = target_date or get_current_local_time().date()

    slots = []
    for slot_def in DAILY_SLOTS_JORDAN_TIME:
        hour, minute = map(int, slot_def["time_str"].split(":"))
        local_dt = datetime.combine(today, dtime(hour=hour, minute=minute), tzinfo=tz)
        utc_dt = local_dt.astimezone(timezone.utc)

        slots.append({
            **slot_def,
            "scheduled_local": local_dt,
            "scheduled_utc": utc_dt,
        })

    return slots
