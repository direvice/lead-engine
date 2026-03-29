"""APScheduler autonomous jobs."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import get_settings
from database import SessionLocal
from models import BusinessLead, ScanJob
from outreach.digest import build_morning_digest_html
from outreach.email import send_email_smtp
from services.pipeline import analyze_lead_row
from services.scan_job import ScanRequest, get_ai_router, run_scan_job

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None

CATEGORY_ROTATION = [
    ["restaurant", "cafe", "bar", "bakery"],
    ["clothing_store", "jewelry_store", "book_store", "furniture_store"],
    ["hair_care", "beauty_salon", "spa", "gym"],
    ["lawyer", "accounting", "real_estate_agency", "insurance_agency"],
    ["dentist", "doctor", "veterinary_care", "physiotherapist"],
    ["plumber", "electrician", "general_contractor", "locksmith"],
]


def _rotation_index() -> int:
    return (datetime.utcnow().day % len(CATEGORY_ROTATION))


async def job_nightly_category_scan():
    settings = get_settings()
    if not settings.scan_schedule_enabled:
        return
    cats = CATEGORY_ROTATION[_rotation_index()]
    req = ScanRequest(
        location=settings.default_location,
        radius_miles=settings.default_radius_miles,
        categories=list(cats),
    )
    db = SessionLocal()
    job = ScanJob(
        location=req.location,
        radius_miles=req.radius_miles,
        categories=req.categories,
        status="running",
        message="Scheduled nightly scan",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    jid = job.id
    db.close()
    await run_scan_job(jid, req)


async def job_rescan_stale():
    settings = get_settings()
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(BusinessLead)
        .filter(
            BusinessLead.last_analyzed_at.isnot(None),
            BusinessLead.last_analyzed_at < cutoff,
            BusinessLead.site_improved == False,  # noqa: E712
        )
        .limit(15)
        .all()
    )
    sem = asyncio.Semaphore(settings.max_concurrent_scrapers)
    router = get_ai_router()
    for lead in rows:
        try:
            await analyze_lead_row(db, lead, router, sem)
        except Exception as e:
            logger.warning("Rescan lead %s: %s", lead.id, e)
    db.close()


async def job_morning_digest():
    settings = get_settings()
    if not settings.gmail_address or not settings.gmail_app_password:
        return
    if not settings.digest_recipient:
        return
    db = SessionLocal()
    since = datetime.utcnow() - timedelta(hours=14)
    new_leads = (
        db.query(BusinessLead)
        .filter(BusinessLead.created_at >= since)
        .order_by(BusinessLead.revenue_opportunity_monthly.desc().nullslast())
        .limit(20)
        .all()
    )
    items = [
        {
            "id": L.id,
            "business_name": L.business_name,
            "category": L.category,
            "city": L.address,
            "lead_score": L.lead_score,
            "revenue_opportunity_monthly": L.revenue_opportunity_monthly,
            "ai_biggest_problem": L.ai_biggest_problem,
            "ai_pitch": L.ai_pitch,
            "phone": L.phone,
        }
        for L in new_leads
    ]
    top_name = items[0]["business_name"] if items else "—"
    top_rev = (items[0].get("revenue_opportunity_monthly") or 0) if items else 0
    html = build_morning_digest_html(
        new_leads=items,
        scanned_count=len(items),
        category=", ".join(CATEGORY_ROTATION[_rotation_index()]),
        dashboard_url="http://localhost:3000",
        next_scan_hint=f"Tonight ~2am: {', '.join(CATEGORY_ROTATION[_rotation_index()])}",
    )
    subject = f"🎯 {len(items)} new leads — top: {top_name} (${top_rev:,}/mo)"
    try:
        send_email_smtp(
            host="smtp.gmail.com",
            port=587,
            user=settings.gmail_address,
            password=settings.gmail_app_password,
            to_addrs=[settings.digest_recipient],
            subject=subject,
            body_html=html,
        )
    except Exception as e:
        logger.warning("Digest email failed: %s", e)
    db.close()


def start_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        return
    scheduler = AsyncIOScheduler()
    scheduler.add_job(job_nightly_category_scan, "cron", hour=2, minute=0, id="nightly_scan")
    scheduler.add_job(job_rescan_stale, "cron", hour=3, minute=0, id="rescan_stale")
    scheduler.add_job(job_morning_digest, "cron", hour=7, minute=30, id="morning_digest")
    scheduler.add_job(job_nightly_category_scan, "cron", hour=12, minute=0, id="noon_quick")
    scheduler.start()
    logger.info("APScheduler started")
