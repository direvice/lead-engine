"""Background scan job + shared AI router (avoids circular imports)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from ai.gemini_client import GeminiClient
from ai.ollama_client import OllamaClient
from ai.router import AIRouter
from config import get_settings
from database import SessionLocal
from models import BusinessLead, ScanJob
from services.geocode import resolve_coordinates
from services.pipeline import analyze_lead_row, discover_all

logger = logging.getLogger(__name__)

active_scan_message: str = ""

_ai_router: AIRouter | None = None


def get_ai_router() -> AIRouter:
    global _ai_router
    if _ai_router is None:
        s = get_settings()
        ollama = OllamaClient(s.ollama_host)
        gemini = GeminiClient(s.gemini_api_key) if s.gemini_api_key else None
        _ai_router = AIRouter(ollama, gemini)
    return _ai_router


class ScanRequest(BaseModel):
    location: str = Field(default_factory=lambda: get_settings().default_location)
    radius_miles: float = Field(default_factory=lambda: get_settings().default_radius_miles)
    categories: list[str] = Field(
        default_factory=lambda: ["restaurant", "cafe", "beauty_salon"]
    )


async def run_scan_job(job_id: int, req: ScanRequest) -> None:
    global active_scan_message

    active_scan_message = "Starting…"
    db = SessionLocal()
    router = get_ai_router()
    try:
        job = db.get(ScanJob, job_id)
        if not job:
            return
        s = get_settings()
        coords = resolve_coordinates(
            req.location, s.google_places_api_key, s.geoapify_api_key
        )
        if not coords:
            job.status = "failed"
            job.message = (
                "Geocode failed — try a clearer location (e.g. City, ST, USA). "
                "Set GEOAPIFY_API_KEY or GOOGLE_PLACES_API_KEY, or rely on OSM Nominatim/Photon."
            )
            db.commit()
            return
        lat, lng = coords
        businesses = await discover_all(
            lat=lat,
            lng=lng,
            location_label=req.location,
            radius_miles=req.radius_miles,
            categories_filter=req.categories or None,
        )
        job.progress_total = len(businesses)
        job.message = f"Analyzing {len(businesses)} businesses"
        db.commit()

        sem = asyncio.Semaphore(get_settings().max_concurrent_scrapers)

        def upsert_lead(b: dict[str, Any]) -> BusinessLead:
            pid = b.get("place_id")
            phone = b.get("phone")
            existing = None
            if pid:
                existing = (
                    db.query(BusinessLead)
                    .filter(BusinessLead.place_id == pid)
                    .first()
                )
            if not existing and phone:
                existing = (
                    db.query(BusinessLead)
                    .filter(BusinessLead.phone == phone)
                    .first()
                )
            if existing:
                existing.business_name = b.get("business_name") or existing.business_name
                existing.address = b.get("address") or existing.address
                existing.website = b.get("website") or existing.website
                existing.google_rating = b.get("google_rating") or existing.google_rating
                existing.review_count = b.get("review_count") or existing.review_count
                existing.category = b.get("category") or existing.category
                existing.latitude = b.get("latitude") or existing.latitude
                existing.longitude = b.get("longitude") or existing.longitude
                existing.source = b.get("source", "merged")
                existing.source_ids = {
                    **(existing.source_ids or {}),
                    **(b.get("source_ids") or {}),
                }
                db.commit()
                db.refresh(existing)
                return existing
            lead = BusinessLead(
                place_id=pid,
                business_name=b.get("business_name") or "Unknown",
                address=b.get("address"),
                category=b.get("category"),
                phone=phone,
                website=b.get("website"),
                latitude=b.get("latitude"),
                longitude=b.get("longitude"),
                google_rating=b.get("google_rating"),
                review_count=b.get("review_count"),
                business_status=b.get("business_status"),
                source=b.get("source", "merged"),
                source_ids=b.get("source_ids"),
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            return lead

        leads_found = 0
        for i, b in enumerate(businesses):
            active_scan_message = (
                f"Analyzing {i+1}/{len(businesses)}: {b.get('business_name')}"
            )
            job.progress_current = i + 1
            db.commit()
            lead = upsert_lead(b)
            try:
                await analyze_lead_row(db, lead, router, sem)
                leads_found += 1
            except Exception as e:
                logger.exception("Lead analyze error: %s", e)
        job.status = "done"
        job.finished_at = datetime.utcnow()
        job.leads_found = leads_found
        job.message = "Complete"
        db.commit()
    finally:
        active_scan_message = ""
        db.close()
