"""
FastAPI Admin API and Web Service for Daily Dhikr Automation.
Provides endpoints for content verification, approvals, graphic preview generation,
publication queue monitoring, and manual note actions.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query, Response, status, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db, init_db, check_db_connection
from app.models import (
    ContentItem,
    SourceRecord,
    PublicationJob,
    JobStatus,
    ApprovalStatus,
    VerificationStatus,
    PublicationType,
    ContentCategory,
    AuditLog,
)
from app.schemas import (
    ContentItemResponse,
    ContentItemCreate,
    PublicationJobResponse,
    SourceRecordResponse,
)
from app.content.verification import validate_content_item
from app.content.library import verify_content, approve_content
from app.graphics.renderer import renderer
from app.publishing.notes import format_note_text, get_manual_note_instructions
from app.scheduler.timezone import get_current_local_time
from app.scheduler.queue import get_due_jobs

app = FastAPI(
    title="Daily Dhikr Automation API",
    description="Operational API for managing automated daily Islamic reminders for Instagram.",
    version="1.0.0"
)

# Template configuration
templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health_check():
    """Health check for deployment monitoring."""
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database_connected": db_ok,
        "local_time_amman": get_current_local_time().isoformat(),
        "dry_run": settings.DRY_RUN,
        "publishing_enabled": settings.PUBLISHING_ENABLED,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard_view(request: Request, db: Session = Depends(get_db)):
    """Renders the administrative web dashboard."""
    now_amman = get_current_local_time()
    due_jobs = get_due_jobs(db, reference_time=now_amman)
    recent_jobs = db.query(PublicationJob).order_by(PublicationJob.scheduled_at.desc()).limit(15).all()
    content_items = db.query(ContentItem).order_by(ContentItem.created_at.desc()).limit(20).all()
    audit_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()

    # Find today's note job
    today_note_job = (
        db.query(PublicationJob)
        .filter(PublicationJob.publication_type == PublicationType.NOTE)
        .order_by(PublicationJob.scheduled_at.desc())
        .first()
    )
    note_text = format_note_text(today_note_job.content) if (today_note_job and today_note_job.content) else "سبحان الله وبحمده"
    note_instructions = get_manual_note_instructions(note_text)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "now_amman": now_amman,
            "due_count": len(due_jobs),
            "recent_jobs": recent_jobs,
            "content_items": content_items,
            "audit_logs": audit_logs,
            "today_note": note_text,
            "note_instructions": note_instructions,
            "today_note_job": today_note_job,
            "dry_run": settings.DRY_RUN,
            "publishing_enabled": settings.PUBLISHING_ENABLED,
        }
    )


@app.get("/api/status")
def get_status(db: Session = Depends(get_db)):
    """Returns detailed system status and queue statistics."""
    now_amman = get_current_local_time()
    due = get_due_jobs(db, reference_time=now_amman)
    published_count = db.query(PublicationJob).filter(PublicationJob.status == JobStatus.PUBLISHED).count()
    failed_count = db.query(PublicationJob).filter(PublicationJob.status == JobStatus.FAILED).count()
    awaiting_note_count = db.query(PublicationJob).filter(PublicationJob.status == JobStatus.AWAITING_MANUAL_ACTION).count()

    return {
        "timezone": settings.TIMEZONE,
        "current_time_amman": now_amman.isoformat(),
        "dry_run": settings.DRY_RUN,
        "publishing_enabled": settings.PUBLISHING_ENABLED,
        "jobs_due_now": len(due),
        "total_published": published_count,
        "total_failed": failed_count,
        "awaiting_manual_notes": awaiting_note_count,
    }


@app.post("/api/settings/toggle-publishing")
def toggle_publishing(enable: bool = Query(...)):
    """Toggles the global master publishing kill switch."""
    settings.PUBLISHING_ENABLED = enable
    return {"publishing_enabled": settings.PUBLISHING_ENABLED}


@app.get("/api/content", response_model=List[ContentItemResponse])
def list_content_items(
    approval: Optional[ApprovalStatus] = None,
    category: Optional[ContentCategory] = None,
    db: Session = Depends(get_db)
):
    """Lists content items with optional filters."""
    query = db.query(ContentItem)
    if approval:
        query = query.filter(ContentItem.approval_status == approval)
    if category:
        query = query.filter(ContentItem.category == category)
    return query.order_by(ContentItem.created_at.desc()).all()


@app.post("/api/content/{content_id}/verify")
def verify_content_endpoint(
    content_id: str,
    verified_by: str = Query("Admin"),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Verifies a content item and its source record."""
    try:
        item = verify_content(db, content_id, verified_by=verified_by, notes=notes)
        db.commit()
        return {"status": "verified", "id": item.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/content/{content_id}/approve")
def approve_content_endpoint(
    content_id: str,
    approver: str = Query("Admin"),
    db: Session = Depends(get_db)
):
    """Approves a verified content item for scheduling."""
    try:
        item = approve_content(db, content_id, approver=approver)
        db.commit()
        return {"status": "approved", "id": item.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/preview/{content_id}")
def preview_rendered_graphic(
    content_id: str,
    template: str = Query("feed_post", description="Template: feed_post, morning_story, evening_story, dua_story"),
    db: Session = Depends(get_db)
):
    """Generates and streams an image preview for a given content item."""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    try:
        image_path, checksum, w, h = renderer.render(item, template_name=template)
        return FileResponse(
            str(image_path),
            media_type="image/jpeg",
            filename=f"preview_{template}_{item.id[:8]}.jpg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")


@app.get("/api/notes/today")
def get_today_note(db: Session = Depends(get_db)):
    """Returns the prepared Instagram Note text with manual publication instructions."""
    job = (
        db.query(PublicationJob)
        .filter(PublicationJob.publication_type == PublicationType.NOTE)
        .order_by(PublicationJob.scheduled_at.desc())
        .first()
    )
    if not job or not job.content:
        raise HTTPException(status_code=404, detail="No Note job currently scheduled.")

    note_text = format_note_text(job.content)
    return {
        "job_id": job.id,
        "status": job.status.value,
        "note_text": note_text,
        "length": len(note_text),
        "max_length": 60,
        "instructions": get_manual_note_instructions(note_text),
    }


@app.post("/api/jobs/{job_id}/mark-note-posted")
def mark_note_as_posted(job_id: str, db: Session = Depends(get_db)):
    """Marks an Instagram Note job as PUBLISHED after manual posting in the app."""
    job = db.query(PublicationJob).filter(PublicationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.PUBLISHED
    job.published_at = datetime.now(timezone.utc)
    job.last_error = "Manually marked as published by administrator."
    db.commit()
    return {"status": "success", "job_id": job.id}
