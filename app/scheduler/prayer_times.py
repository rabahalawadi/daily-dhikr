"""
Prayer times calculation and daily slot scheduler for Daily Dhikr.
Dynamically schedules daily reminders based on Islamic prayer times for Amman, Jordan
(or any configured city/coordinates).

Primary: Aladhan API with disk caching.
Fallback: Built-in astronomical solar calculation (zero external dependencies).
"""

import json
import logging
import math
import os
import urllib.request
import urllib.error
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo

try:
    from app.models import PublicationType, ContentCategory
except (ImportError, ModuleNotFoundError):
    from enum import Enum

    class PublicationType(str, Enum):
        FEED_POST = "feed_post"
        STORY_POST = "story_post"
        NOTE = "note"

    class ContentCategory(str, Enum):
        MORNING_DHIKR = "morning_dhikr"
        EVENING_DHIKR = "evening_dhikr"
        DAILY_REMINDER = "daily_reminder"
        DUA = "dua"
        NOTE = "note"

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).resolve().parent.parent.parent / "assets" / "prayer_times_cache.json"


def calculate_astronomical_prayer_times(
    target_date: date,
    lat: float = 31.9539,
    lon: float = 35.9106,
    fajr_angle: float = 18.5,
    isha_angle: float = 18.0,
    tz_offset: float = 3.0,
) -> Dict[str, str]:
    """
    Computes astronomical prayer times locally without internet or external libraries.
    Based on solar position formulas (Jean Meeus / NOAA standard).
    """
    day_of_year = target_date.timetuple().tm_yday
    # Fractional year in radians
    b = 2.0 * math.pi * (day_of_year - 81) / 365.0
    # Equation of time in minutes
    eot = 9.87 * math.sin(2.0 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    # Solar declination in radians
    decl = math.asin(math.sin(math.radians(23.45)) * math.sin(b))

    # Solar noon in hours (local time)
    noon = 12.0 + (tz_offset - lon / 15.0) - (eot / 60.0)
    lat_rad = math.radians(lat)

    def hour_angle(alpha_deg: float) -> float:
        alpha_rad = math.radians(alpha_deg)
        denom = math.cos(lat_rad) * math.cos(decl)
        if denom == 0:
            return 0.0
        cos_omega = (math.sin(alpha_rad) - math.sin(lat_rad) * math.sin(decl)) / denom
        if cos_omega > 1.0:
            return 0.0
        if cos_omega < -1.0:
            return math.pi
        return math.acos(cos_omega)

    # Fajr
    ha_fajr = hour_angle(-fajr_angle)
    fajr = noon - math.degrees(ha_fajr) / 15.0

    # Sunrise & Sunset (accounting for atmospheric refraction & solar disc: -0.8333 deg)
    ha_sun = hour_angle(-0.8333)
    sunrise = noon - math.degrees(ha_sun) / 15.0
    sunset = noon + math.degrees(ha_sun) / 15.0

    # Asr (Standard Shafi/Hanbali/Maliki: shadow length = object height + noon shadow)
    angle_asr = math.degrees(math.atan(1.0 + math.tan(abs(lat_rad - decl))))
    ha_asr = hour_angle(90.0 - angle_asr)
    asr = noon + math.degrees(ha_asr) / 15.0

    # Isha (either angle-based or 90 mins after Maghrib)
    ha_isha = hour_angle(-isha_angle)
    isha = noon + math.degrees(ha_isha) / 15.0
    # In Umm al-Qura standard, Isha is sunset + 1.5 hours
    isha_umm_alqura = sunset + 1.5
    final_isha = max(isha, isha_umm_alqura)

    def to_time_str(h: float) -> str:
        hrs = int(h) % 24
        mins = int(round((h - int(h)) * 60))
        if mins >= 60:
            hrs = (hrs + 1) % 24
            mins -= 60
        return f"{hrs:02d}:{mins:02d}"

    return {
        "Fajr": to_time_str(fajr),
        "Sunrise": to_time_str(sunrise),
        "Dhuhr": to_time_str(noon),
        "Asr": to_time_str(asr),
        "Sunset": to_time_str(sunset),
        "Maghrib": to_time_str(sunset),
        "Isha": to_time_str(final_isha),
    }


def _load_cache() -> Dict[str, Any]:
    """Loads prayer times cache from disk."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read prayer times cache: {e}")
    return {}


def _save_cache(cache_data: Dict[str, Any]) -> None:
    """Saves prayer times cache to disk."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to write prayer times cache: {e}")


def fetch_prayer_times_from_api(
    target_date: date,
    city: str = "Amman",
    country: str = "Jordan",
    method: int = 4,
) -> Optional[Dict[str, str]]:
    """
    Fetches official prayer times from Aladhan API.
    Returns dictionary with timings or None on failure.
    """
    date_str = target_date.strftime("%d-%m-%Y")
    url = f"https://api.aladhan.com/v1/timingsByCity/{date_str}?city={urllib.parse.quote(city)}&country={urllib.parse.quote(country)}&method={method}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DailyDhikrAutomation/1.0 (Islamic Scheduler)"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                timings = body.get("data", {}).get("timings", {})
                # Clean up any trailing timezone notes (e.g., '05:20 (EEST)' -> '05:20')
                clean_timings = {}
                for k, v in timings.items():
                    clean_timings[k] = v.split()[0]
                logger.info(f"Successfully fetched prayer times for {city}, {country} ({date_str}) from Aladhan API.")
                return clean_timings
    except Exception as exc:
        logger.warning(f"Aladhan API request failed: {exc}. Using fallback calculation.")
    return None


def get_prayer_times_for_date(
    target_date: date,
    city: str = "Amman",
    country: str = "Jordan",
    lat: float = 31.9539,
    lon: float = 35.9106,
    method: int = 4,
    tz_offset: float = 3.0,
) -> Dict[str, str]:
    """
    Returns prayer times for target_date.
    Checks disk cache -> Aladhan API -> Astronomical fallback.
    """
    date_key = f"{city}_{country}_{target_date.isoformat()}"
    cache = _load_cache()

    # 1. Return from cache if present
    if date_key in cache:
        return cache[date_key]

    # 2. Try online API
    timings = fetch_prayer_times_from_api(target_date, city=city, country=country, method=method)
    if timings:
        cache[date_key] = timings
        _save_cache(cache)
        return timings

    # 3. Fallback to local astronomical formulas
    timings = calculate_astronomical_prayer_times(target_date, lat=lat, lon=lon, tz_offset=tz_offset)
    cache[date_key] = timings
    _save_cache(cache)
    return timings


def parse_time_str(time_str: str) -> dtime:
    """Parses 'HH:MM' string into datetime.time object."""
    h, m = map(int, time_str.split(":")[:2])
    return dtime(hour=h, minute=m)


def apply_minute_offset(base_time: dtime, offset_minutes: int) -> dtime:
    """Applies a minute offset to a time object."""
    dt = datetime.combine(date(2000, 1, 1), base_time) + timedelta(minutes=offset_minutes)
    return dt.time()


def get_prayer_schedule_slots(
    target_date: date,
    tz: ZoneInfo,
    city: str = "Amman",
    country: str = "Jordan",
    lat: float = 31.9539,
    lon: float = 35.9106,
    method: int = 4,
    fajr_offset: int = 0,
    duha_offset_after_sunrise: int = 90,
    dhuhr_offset: int = 0,
    asr_offset: int = 0,
    isha_offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Builds the 5 daily publication slots aligned with Islamic prayer times:
    1. morning_story -> Fajr prayer (Morning Adhkar / أذكار الصباح)
    2. feed_post      -> Duha / Mid-morning (Verse of the day / Daily Reminder)
    3. reminder_story -> Dhuhr prayer (Supplication / Midday Adhkar)
    4. evening_story  -> Asr prayer (Evening Adhkar / أذكار المساء)
    5. daily_note     -> Isha prayer (Night Reflection / Instagram Note)
    """
    timings = get_prayer_times_for_date(
        target_date,
        city=city,
        country=country,
        lat=lat,
        lon=lon,
        method=method,
    )

    fajr_time = parse_time_str(timings.get("Fajr", "05:20"))
    sunrise_time = parse_time_str(timings.get("Sunrise", "06:45"))
    dhuhr_time = parse_time_str(timings.get("Dhuhr", "12:20"))
    asr_time = parse_time_str(timings.get("Asr", "15:30"))
    isha_time = parse_time_str(timings.get("Isha", "19:25"))

    # Apply offsets
    actual_fajr = apply_minute_offset(fajr_time, fajr_offset)
    actual_duha = apply_minute_offset(sunrise_time, duha_offset_after_sunrise)
    actual_dhuhr = apply_minute_offset(dhuhr_time, dhuhr_offset)
    actual_asr = apply_minute_offset(asr_time, asr_offset)
    actual_isha = apply_minute_offset(isha_time, isha_offset)

    slot_defs = [
        {
            "slot_name": "morning_story",
            "prayer_name": "Fajr",
            "time_obj": actual_fajr,
            "pub_type": PublicationType.STORY_POST,
            "category": ContentCategory.MORNING_DHIKR,
            "template": "morning_story",
            "description": "Morning Adhkar at Fajr prayer",
        },
        {
            "slot_name": "feed_post",
            "prayer_name": "Jumuah_Morning" if target_date.weekday() == 4 else "Duha",
            "time_obj": dtime(6, 0) if target_date.weekday() == 4 else actual_duha,
            "pub_type": PublicationType.FEED_POST,
            "category": ContentCategory.FRIDAY_SPECIAL if target_date.weekday() == 4 else ContentCategory.VERSE_OF_THE_DAY,
            "template": "surah_kahf_carousel" if target_date.weekday() == 4 else "verse_of_the_day",
            "description": "Friday Special / Surat Al-Kahf at 06:00 AM" if target_date.weekday() == 4 else "Verse of the Day at Duha",
        },
        {
            "slot_name": "reminder_story",
            "prayer_name": "Dhuhr",
            "time_obj": actual_dhuhr,
            "pub_type": PublicationType.STORY_POST,
            "category": ContentCategory.DUA,
            "template": "dua_story",
            "description": "Midday Supplication & Dhikr at Dhuhr prayer",
        },
        {
            "slot_name": "evening_story",
            "prayer_name": "Asr",
            "time_obj": actual_asr,
            "pub_type": PublicationType.STORY_POST,
            "category": ContentCategory.EVENING_DHIKR,
            "template": "evening_story",
            "description": "Evening Adhkar at Asr prayer (Sunnah start of evening remembrance)",
        },
        {
            "slot_name": "daily_note",
            "prayer_name": "Isha",
            "time_obj": actual_isha,
            "pub_type": PublicationType.NOTE,
            "category": ContentCategory.NOTE,
            "template": None,
            "description": "Night Reflection / Instagram Note draft at Isha prayer",
        },
    ]

    slots = []
    for s in slot_defs:
        time_o = s["time_obj"]
        local_dt = datetime.combine(target_date, time_o, tzinfo=tz)
        utc_dt = local_dt.astimezone(timezone.utc)
        slots.append({
            "slot_name": s["slot_name"],
            "prayer_name": s["prayer_name"],
            "time_str": f"{time_o.hour:02d}:{time_o.minute:02d}",
            "pub_type": s["pub_type"],
            "category": s["category"],
            "template": s["template"],
            "description": s["description"],
            "scheduled_local": local_dt,
            "scheduled_utc": utc_dt,
        })

    return slots
