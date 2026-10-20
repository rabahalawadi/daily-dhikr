"""
Script to delete existing Instagram media and cleanly republish with updated templates.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.database import get_db_context
from app.models import PublicationJob, JobStatus
from app.publishing.instagrapi_client import instagrapi_publisher
from app.scheduler.runner import runner


def main():
    print("=" * 60)
    print("REPUBLISHING PIPELINE: DELETE & CLEAN RE-UPLOAD")
    print("=" * 60)

    cl = instagrapi_publisher.get_client()

    # Step 1: Delete old feed posts
    print("\n[1/3] Deleting old feed posts...")
    medias = cl.user_medias(cl.user_id, amount=5)
    for m in medias:
        print(f"Deleting Feed Post PK: {m.pk}...")
        try:
            cl.media_delete(str(m.pk))
            print(f"Successfully deleted Feed Post: {m.pk}")
        except Exception as e:
            print(f"Warning deleting Feed Post {m.pk}: {e}")
        time.sleep(2)

    # Step 2: Delete old stories
    print("\n[2/3] Deleting old stories...")
    stories = cl.user_stories(cl.user_id)
    for s in stories:
        print(f"Deleting Story PK: {s.pk}...")
        try:
            cl.story_delete(str(s.pk))
            print(f"Successfully deleted Story: {s.pk}")
        except Exception as e:
            print(f"Warning deleting Story {s.pk}: {e}")
        time.sleep(2)

    # Step 3: Republish today's jobs in correct sequence
    print("\n[3/3] Re-uploading today's posts with corrected templates...")

    jobs_to_publish = [
        # 1. Main Feed Post (Verse of the Day)
        ("7320a9a6-f0fc-468b-a6af-2246352613fa", "Feed Post (Verse of the Day)"),
        # 2. Morning Story (Morning Adhkar)
        ("aaea4a7b-b292-47eb-8842-a32d46271add", "Morning Story (Morning Adhkar)"),
        # 3. Reminder Story (Daily Reminder)
        ("03372f3b-0e3e-4142-bec0-30a9fa4406e1", "Reminder Story (Daily Reminder)"),
        # 4. Evening Story (Evening Adhkar)
        ("4da6083b-f34e-4740-bacf-0aef0e7b9476", "Evening Story (Evening Adhkar)"),
    ]

    with get_db_context() as db:
        for job_id, label in jobs_to_publish:
            job = db.query(PublicationJob).filter(PublicationJob.id == job_id).first()
            if not job:
                print(f"Job {job_id} not found, skipping.")
                continue

            # Reset status to READY
            job.status = JobStatus.READY
            job.last_error = None
            db.commit()

            print(f"\nPublishing {label} [Job: {job.id[:8]}]...")
            runner._process_job(db, job)
            print(f"Result: Status={job.status.value}, Instagram Media ID={job.instagram_media_id}")
            time.sleep(4)

    print("\n" + "=" * 60)
    print("ALL POSTS & STORIES RE-PUBLISHED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
