import sys
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import date

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scheduler.prayer_times import get_prayer_schedule_slots, get_prayer_times_for_date

def main():
    tz = ZoneInfo("Asia/Amman")
    today = date(2026, 10, 21)
    timings = get_prayer_times_for_date(today)
    print("==================================================")
    print("Official / Calculated Prayer Times in Amman, Jordan:")
    print("==================================================")
    for k, v in timings.items():
        print(f"  {k:10}: {v}")

    print("\n==================================================")
    print("Daily Dhikr Prayer-Aligned Schedule:")
    print("==================================================")
    slots = get_prayer_schedule_slots(today, tz)
    for s in slots:
        local_str = s['scheduled_local'].strftime('%H:%M %Z')
        utc_str = s['scheduled_utc'].strftime('%H:%M UTC')
        print(f"  {s['prayer_name']:6} ({s['time_str']}) -> {s['slot_name']:15} [{s['pub_type']}]")
        print(f"         Local Time: {local_str} | UTC: {utc_str}")
        print(f"         Category:   {s['category']}")
        print(f"         Note:       {s['description']}\n")

if __name__ == "__main__":
    main()
