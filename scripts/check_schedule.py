import sys
import os
sys.path.insert(0, os.path.abspath("."))
import zoneinfo
from datetime import datetime
from app.database import get_db_context
from app.models import PublicationJob, ContentItem

tz = zoneinfo.ZoneInfo("Asia/Amman")
now = datetime.now(tz)
print(f"Current Amman time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

with get_db_context() as db:
    jobs = (
        db.query(PublicationJob, ContentItem)
        .join(ContentItem, PublicationJob.content_id == ContentItem.id)
        .order_by(PublicationJob.scheduled_at.desc())
        .limit(10)
        .all()
    )
    print("Latest 10 Publication Jobs:")
    for job, item in reversed(jobs):
        local_time = job.scheduled_at.astimezone(tz).strftime('%Y-%m-%d %H:%M')
        print(f" - [{job.status.value:9s}] {item.category.value:18s} ({job.publication_type.value:10s}) | Scheduled: {local_time} | ID: {job.id[:8]}")
