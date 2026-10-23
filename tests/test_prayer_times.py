"""
Unit tests for Islamic prayer times calculation and dynamic scheduling engine.
"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
import pytest

from app.scheduler.prayer_times import (
    calculate_astronomical_prayer_times,
    get_prayer_times_for_date,
    get_prayer_schedule_slots,
    apply_minute_offset,
    parse_time_str,
)
from app.models import PublicationType, ContentCategory


def test_astronomical_prayer_calculation_amman():
    """Verifies that the offline astronomical formula computes realistic prayer times for Amman."""
    target = date(2026, 10, 21)
    # Amman coordinates: Lat 31.9539, Lon 35.9106, UTC+3
    times = calculate_astronomical_prayer_times(target, lat=31.9539, lon=35.9106, tz_offset=3.0)

    assert "Fajr" in times
    assert "Sunrise" in times
    assert "Dhuhr" in times
    assert "Asr" in times
    assert "Maghrib" in times
    assert "Isha" in times

    # In October in Amman:
    # Fajr is around 05:20-05:30
    fajr_h, fajr_m = map(int, times["Fajr"].split(":"))
    assert fajr_h == 5
    assert 10 <= fajr_m <= 40

    # Dhuhr is around 12:15-12:30
    dhuhr_h, dhuhr_m = map(int, times["Dhuhr"].split(":"))
    assert dhuhr_h == 12
    assert 15 <= dhuhr_m <= 35

    # Maghrib is around 17:45-18:05
    maghrib_h, maghrib_m = map(int, times["Maghrib"].split(":"))
    assert maghrib_h in (17, 18)


def test_prayer_schedule_slots_alignment():
    """
    Verifies that the 5 daily publication slots are properly mapped to Islamic prayers:
    - morning_story -> Fajr (Morning Adhkar)
    - feed_post     -> Duha (Daily Reminder)
    - reminder_story-> Dhuhr (Supplication)
    - evening_story -> Asr (Evening Adhkar)
    - daily_note    -> Isha (Night Reflection)
    """
    tz = ZoneInfo("Asia/Amman")
    target = date(2026, 10, 21)
    slots = get_prayer_schedule_slots(target, tz)

    assert len(slots) == 5

    slot_map = {s["slot_name"]: s for s in slots}

    # 1. Morning Story at Fajr
    morning = slot_map["morning_story"]
    assert morning["prayer_name"] == "Fajr"
    assert morning["pub_type"] == PublicationType.STORY_POST
    assert morning["category"] == ContentCategory.MORNING_DHIKR
    assert morning["template"] == "morning_story"
    # Fajr is around 05:00-05:30 Amman time
    assert morning["scheduled_local"].hour == 5

    # 2. Feed Post at Duha
    feed = slot_map["feed_post"]
    assert feed["prayer_name"] == "Duha"
    assert feed["pub_type"] == PublicationType.FEED_POST
    assert feed["category"] in (ContentCategory.DAILY_REMINDER, ContentCategory.VERSE_OF_THE_DAY)
    assert feed["template"] in ("feed_post", "verse_of_the_day")
    assert feed["scheduled_local"].hour == 8

    # 3. Reminder Story at Dhuhr
    reminder = slot_map["reminder_story"]
    assert reminder["prayer_name"] == "Dhuhr"
    assert reminder["pub_type"] == PublicationType.STORY_POST
    assert reminder["category"] == ContentCategory.DUA
    assert reminder["template"] == "dua_story"
    assert reminder["scheduled_local"].hour == 12

    # 4. Evening Story at Asr (Sunnah time for evening adhkar)
    evening = slot_map["evening_story"]
    assert evening["prayer_name"] == "Asr"
    assert evening["pub_type"] == PublicationType.STORY_POST
    assert evening["category"] == ContentCategory.EVENING_DHIKR
    assert evening["template"] == "evening_story"
    assert evening["scheduled_local"].hour == 15

    # 5. Daily Note at Isha
    note = slot_map["daily_note"]
    assert note["prayer_name"] == "Isha"
    assert note["pub_type"] == PublicationType.NOTE
    assert note["category"] == ContentCategory.NOTE
    assert note["scheduled_local"].hour == 19


def test_prayer_schedule_offsets():
    """Ensures offsets adjust the prayer scheduled time properly."""
    tz = ZoneInfo("Asia/Amman")
    target = date(2026, 10, 21)

    # Add +15 mins to Fajr
    slots = get_prayer_schedule_slots(target, tz, fajr_offset=15)
    slot_map = {s["slot_name"]: s for s in slots}

    # If base Fajr was 05:20, +15 mins should be 05:35
    assert slot_map["morning_story"]["time_str"] in ("05:35", "05:36", "05:39")
