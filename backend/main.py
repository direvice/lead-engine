"""FastAPI application — Lead Engine API."""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from config import get_settings, parse_cors_origins
from database import get_db, init_db
from models import BusinessLead, ScanJob
from services.learning_engine import (
    intelligence_brief,
    recalculate_all_scores,
    record_teaching_signal,
)
from services.scan_job import ScanRequest, active_scan_message, get_ai_router, run_scan_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
os.makedirs(settings.screenshot_dir, exist_ok=True)
os.makedirs(settings.audio_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        from scheduler import start_scheduler

        if settings.scan_schedule_enabled:
            start_scheduler()
    except Exception as e:
        logger.warning("Scheduler not started: %s", e)
    yield


app = FastAPI(title="Lead Engine API", lifespan=lifespan)
# Explicit origins from CORS_ORIGINS + regex so any Vercel deployment URL works (CLI previews use unique *.vercel.app hosts).
_VERCEL_REGEX = r"^https://[a-zA-Z0-9\-.]+\.vercel\.app$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(settings.cors_origins),
    allow_origin_regex=_VERCEL_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static/screenshots",
    StaticFiles(directory=settings.screenshot_dir),
    name="screenshots",
)
app.mount(
    "/static/audio",
    StaticFiles(directory=settings.audio_dir),
    name="audio",
)


def _lead_to_dict(lead: BusinessLead) -> dict[str, Any]:
    d = {c.name: getattr(lead, c.name) for c in lead.__table__.columns}
    if d.get("created_at"):
        d["created_at"] = d["created_at"].isoformat()
    if d.get("updated_at"):
        d["updated_at"] = d["updated_at"].isoformat()
    if d.get("last_analyzed_at"):
        d["last_analyzed_at"] = d["last_analyzed_at"].isoformat()
    if d.get("last_screenshoted"):
        d["last_screenshoted"] = d["last_screenshoted"].isoformat()
    return d


class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class TeachBody(BaseModel):
    signal: str  # good_target | bad_target


VALID_TEACH = frozenset({"good_target", "bad_target"})


@app.get("/api/ping")
def ping():
    """Fast liveness check for load balancers (no external I/O)."""
    return {"ok": True}


@app.get("/api/health")
async def health():
    r = get_ai_router()
    ollama_ok = await r.ollama.is_available()
    gemini_ok = bool(r.gemini and r.gemini.configured())
    return {"ok": True, "ollama": ollama_ok, "gemini": gemini_ok}


@app.get("/api/stats")
def api_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(BusinessLead.id)).scalar() or 0
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_week = (
        db.query(func.count(BusinessLead.id))
        .filter(BusinessLead.created_at >= week_ago)
        .scalar()
        or 0
    )
    opp = db.query(func.sum(BusinessLead.revenue_opportunity_monthly)).scalar() or 0
    avg = db.query(func.avg(BusinessLead.lead_score)).scalar() or 0
    return {
        "total_leads": total,
        "new_this_week": new_week,
        "total_monthly_opportunity": int(opp),
        "avg_lead_score": round(float(avg), 1),
    }


@app.get("/api/leads")
def list_leads(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    status: Optional[str] = None,
    min_score: float = 0,
    category: Optional[str] = None,
    source: Optional[str] = None,
    sort: str = "lead_score",
    smb_tier: Optional[str] = None,
    exclude_likely_chain: bool = False,
    limit: int = Query(100, le=500),
    offset: int = 0,
):
    query = db.query(BusinessLead)
    if q:
        like = f"%{q}%"
        query = query.filter(BusinessLead.business_name.ilike(like))
    if status:
        query = query.filter(BusinessLead.status == status)
    if min_score:
        query = query.filter(BusinessLead.lead_score >= min_score)
    if category:
        query = query.filter(BusinessLead.category.ilike(f"%{category}%"))
    if source and source != "all":
        query = query.filter(
            or_(
                BusinessLead.source == source,
                BusinessLead.source_ids.isnot(None),
            )
        )
    tier_json = func.json_extract(BusinessLead.features, "$.smb_fit.target_tier")
    if smb_tier:
        query = query.filter(tier_json == smb_tier)
    if exclude_likely_chain:
        query = query.filter(
            or_(
                BusinessLead.features.is_(None),
                func.coalesce(tier_json, "") != "likely_chain",
            )
        )
    smb_idx_json = func.json_extract(BusinessLead.features, "$.smb_fit.smb_fit_index")
    if sort == "revenue":
        query = query.order_by(BusinessLead.revenue_opportunity_monthly.desc().nullslast())
    elif sort == "newest":
        query = query.order_by(BusinessLead.created_at.desc())
    elif sort == "name":
        query = query.order_by(BusinessLead.business_name)
    elif sort == "smb_fit":
        query = query.order_by(smb_idx_json.desc().nullslast())
    else:
        query = query.order_by(BusinessLead.lead_score.desc().nullslast())
    rows = query.offset(offset).limit(limit).all()
    return {"items": [_lead_to_dict(r) for r in rows], "count": len(rows)}


@app.get("/api/leads/export.csv")
def export_leads_csv(
    db: Session = Depends(get_db),
    min_score: float = 0,
    exclude_likely_chain: bool = False,
):
    query = db.query(BusinessLead)
    if min_score:
        query = query.filter(BusinessLead.lead_score >= min_score)
    tier_json = func.json_extract(BusinessLead.features, "$.smb_fit.target_tier")
    if exclude_likely_chain:
        query = query.filter(
            or_(
                BusinessLead.features.is_(None),
                func.coalesce(tier_json, "") != "likely_chain",
            )
        )
    rows = (
        query.order_by(BusinessLead.lead_score.desc().nullslast()).limit(2500).all()
    )
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "id",
            "business_name",
            "category",
            "address",
            "phone",
            "website",
            "lead_score",
            "smb_tier",
            "smb_fit_index",
            "status",
            "revenue_monthly",
        ]
    )
    for r in rows:
        feats = r.features if isinstance(r.features, dict) else {}
        smb = feats.get("smb_fit") or {}
        w.writerow(
            [
                r.id,
                r.business_name,
                r.category or "",
                (r.address or "").replace("\n", " "),
                r.phone or "",
                r.website or "",
                r.lead_score or 0,
                smb.get("target_tier") or "",
                smb.get("smb_fit_index") or "",
                r.status,
                r.revenue_opportunity_monthly or 0,
            ]
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="lead-engine-export.csv"'},
    )


@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(BusinessLead, lead_id)
    if not lead:
        raise HTTPException(404)
    return _lead_to_dict(lead)


@app.patch("/api/leads/{lead_id}")
def patch_lead(lead_id: int, body: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.get(BusinessLead, lead_id)
    if not lead:
        raise HTTPException(404)
    prev = lead.status
    if body.status:
        lead.status = body.status
    if body.notes is not None:
        lead.notes = body.notes
    if body.status and body.status != prev:
        try:
            if body.status == "won":
                record_teaching_signal(db, lead, "outcome_won")
            elif body.status == "skip":
                record_teaching_signal(db, lead, "outcome_skip")
        except Exception as e:
            logger.warning("Learning from status change failed: %s", e)
    db.commit()
    return _lead_to_dict(lead)


@app.post("/api/leads/{lead_id}/teach")
def teach_lead(lead_id: int, body: TeachBody, db: Session = Depends(get_db)):
    if body.signal not in VALID_TEACH:
        raise HTTPException(400, detail="signal must be good_target or bad_target")
    lead = db.get(BusinessLead, lead_id)
    if not lead:
        raise HTTPException(404)
    try:
        meta = record_teaching_signal(db, lead, body.signal)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=str(e)) from e
    return {"ok": True, **meta}


@app.get("/api/intelligence/brief")
def api_intelligence_brief(db: Session = Depends(get_db)):
    return intelligence_brief(db)


@app.post("/api/intelligence/recalculate-scores")
def api_recalculate_scores(db: Session = Depends(get_db)):
    """Re-apply learning multipliers to all leads that have _score_pre_learning stored."""
    return recalculate_all_scores(db)


@app.get("/api/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    # Funnel
    funnel = {}
    for s in ["new", "contacted", "interested", "won", "skip"]:
        funnel[s] = (
            db.query(func.count(BusinessLead.id)).filter(BusinessLead.status == s).scalar()
            or 0
        )
    return {"funnel": funnel}


@app.post("/api/scan")
async def start_scan(req: ScanRequest, db: Session = Depends(get_db)):
    # Scans work without Google: geocode uses OSM Nominatim; discovery uses OSM/Yelp/YP/etc.
    job = ScanJob(
        location=req.location,
        radius_miles=req.radius_miles,
        categories=req.categories,
        status="running",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    asyncio.create_task(run_scan_job(job.id, req))
    return {"job_id": job.id, "status": "started"}


@app.get("/api/scan/{job_id}")
def scan_status(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ScanJob, job_id)
    if not job:
        raise HTTPException(404)
    return {
        "id": job.id,
        "status": job.status,
        "progress_current": job.progress_current,
        "progress_total": job.progress_total,
        "message": job.message,
        "leads_found": job.leads_found,
    }


@app.get("/api/bot-status")
async def bot_status():
    return {
        "message": active_scan_message or "Idle",
        "next_scan_hint": "Scheduled jobs depend on APScheduler",
    }


@app.get("/api/analytics/charts")
def analytics_charts(db: Session = Depends(get_db)):
    by_cat = (
        db.query(BusinessLead.category, func.count(BusinessLead.id))
        .group_by(BusinessLead.category)
        .all()
    )
    return {
        "by_category": [{"name": c or "unknown", "count": n} for c, n in by_cat if c],
        "score_buckets": [],
    }
