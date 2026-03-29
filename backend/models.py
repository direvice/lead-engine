"""Database models."""

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    interested = "interested"
    won = "won"
    skip = "skip"


class BusinessLead(Base):
    __tablename__ = "business_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Identity
    place_id: Mapped[Optional[str]] = mapped_column(String(256), index=True, nullable=True)
    business_name: Mapped[str] = mapped_column(String(512))
    category: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    google_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    business_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    source: Mapped[str] = mapped_column(String(64), default="merged")
    source_ids: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Scrape / tech
    no_website: Mapped[bool] = mapped_column(Boolean, default=False)
    website_builder: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    load_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_horizontal_scroll: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    scrape_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    robots_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Features (JSON blobs for flexibility)
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    issues: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    critical_issues: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    missing_features: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Scores
    opportunity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    technical_debt_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    urgency_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lead_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    seo_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mobile_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Revenue
    revenue_opportunity_monthly: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    revenue_opportunity_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Competitors
    competitors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    competitive_gaps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # PageSpeed
    pagespeed_mobile: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pagespeed_desktop: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lcp_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cls_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fid_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fcp_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    speed_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pagespeed_opportunities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Social
    social_platforms: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    social_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    social_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Screenshots / change
    last_screenshoted: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    screenshot_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    site_improved: Mapped[bool] = mapped_column(Boolean, default=False)
    desktop_screenshot_path: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    mobile_screenshot_path: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    audio_briefing_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    site_age_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # AI
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_biggest_problem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_pitch: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_recommended_service: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    ai_estimated_value: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    ai_revenue_opportunity: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    ai_urgency_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    call_script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_pitch: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # CRM
    status: Mapped[str] = mapped_column(
        String(32), default=LeadStatus.new.value, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    location: Mapped[str] = mapped_column(String(512))
    radius_miles: Mapped[float] = mapped_column(Float)
    categories: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="running")
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    leads_found: Mapped[int] = mapped_column(Integer, default=0)


class ZipScanState(Base):
    __tablename__ = "zip_scan_state"

    zip_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SettingsRow(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)
