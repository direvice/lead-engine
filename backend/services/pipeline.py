"""End-to-end lead analysis pipeline."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from ai.prompts import ANALYSIS_PROMPT, PITCH_PROMPT
from ai.router import AIRouter
from analysis.competitors import find_competitors
from analysis.issues import build_issues
from analysis.revenue import compute_revenue_opportunity
from analysis.scorer import compute_scores
from analysis.smb_fit import assess_smb_fit
from config import get_settings
from discovery.facebook import search_facebook_pages
from discovery.geoapify_places import discover_geoapify_places
from discovery.google_places import discover_google_places
from discovery.merger import merge_business_lists
from discovery.osm import search_osm
from discovery.yellowpages import search_yellowpages
from discovery.yelp import discover_yelp_terms
from models import BusinessLead
from outreach.audio import generate_audio_briefing
from outreach.scripts import generate_call_script
from services.learning_engine import apply_pattern_multiplier
from scraping.browser import WebScraper
from scraping.extractor import copyright_years, extract_text_and_features
from scraping.pagespeed import run_pagespeed
from scraping.social import score_social
from scraping.diff import detect_changes

logger = logging.getLogger(__name__)


def _parse_city(address: str | None) -> str | None:
    if not address:
        return None
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 2:
        return parts[-2]
    return parts[0]


async def discover_all(
    *,
    lat: float,
    lng: float,
    location_label: str,
    radius_miles: float,
    categories_filter: list[str] | None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    radius_m = int(radius_miles * 1609.34)
    groups: list[list[dict[str, Any]]] = []

    gp = discover_google_places(
        settings.google_places_api_key, lat, lng, radius_meters=min(radius_m, 50000)
    )
    groups.append(gp)

    try:
        gfy = await discover_geoapify_places(
            settings.geoapify_api_key, lat, lng, radius_meters=min(radius_m, 50000)
        )
        groups.append(gfy)
    except Exception as e:
        logger.warning("Geoapify: %s", e)

    try:
        osm = await search_osm(lat, lng, radius_meters=min(radius_m, 10000))
        groups.append(osm)
    except Exception as e:
        logger.warning("OSM: %s", e)

    if settings.yelp_api_key:
        try:
            yp = await discover_yelp_terms(settings.yelp_api_key, location_label)
            groups.append(yp)
        except Exception as e:
            logger.warning("Yelp: %s", e)

    if settings.facebook_access_token:
        try:
            fb = await search_facebook_pages(
                settings.facebook_access_token,
                q=categories_filter[0] if categories_filter else "restaurant",
                center=(lat, lng),
            )
            groups.append(fb)
        except Exception as e:
            logger.warning("Facebook: %s", e)

    try:
        yp_web = await search_yellowpages(
            location_label, categories_filter[0] if categories_filter else "restaurants"
        )
        groups.append(yp_web)
    except Exception as e:
        logger.warning("Yellowpages: %s", e)

    merged = merge_business_lists(groups)
    if categories_filter:
        cf = [c.lower() for c in categories_filter]
        merged = [
            m
            for m in merged
            if any(
                c in " ".join(m.get("types") or []).lower()
                or c in (m.get("category") or "").lower()
                for c in cf
            )
        ] or merged
    return merged


async def analyze_lead_row(
    db: Session,
    lead: BusinessLead,
    router: AIRouter,
    sem: asyncio.Semaphore,
) -> None:
    settings = get_settings()
    ollama = OllamaClient(settings.ollama_host)
    scraper = WebScraper()

    website = lead.website
    no_website = not website or not str(website).startswith("http")
    lead.no_website = no_website

    features: dict[str, Any] = {}
    scraped_meta: dict[str, Any] = {}
    html = ""
    pagespeed: dict[str, Any] = {}
    social: dict[str, Any] = {
        "social_score": 0,
        "social_active": False,
        "social_platforms": {},
    }

    async with sem:
        if not no_website:
            data = await scraper.scrape(website, lead.id)
            scraped_meta = {
                "load_error": data.load_error,
                "robots_blocked": data.robots_blocked,
                "page_errors": data.page_errors,
                "has_horizontal_scroll": data.has_horizontal_scroll,
            }
            if data.desktop_path:
                lead.desktop_screenshot_path = data.desktop_path
            if data.mobile_path:
                lead.mobile_screenshot_path = data.mobile_path
            lead.load_time_ms = data.load_time_ms
            if data.load_error or data.robots_blocked:
                lead.scrape_error = data.load_error or "robots"
            html = data.html or ""
            if html:
                features = extract_text_and_features(html, website)
                features["has_horizontal_scroll"] = data.has_horizontal_scroll
                ps_m = await run_pagespeed(website, settings.google_places_api_key, "mobile")
                ps_d = await run_pagespeed(website, settings.google_places_api_key, "desktop")
                pagespeed = ps_m
                lead.pagespeed_mobile = ps_m.get("performance_score")
                lead.pagespeed_desktop = ps_d.get("performance_score")
                lead.lcp_ms = ps_m.get("lcp_ms")
                lead.cls_score = ps_m.get("cls_score")
                lead.fcp_ms = ps_m.get("fcp_ms")
                lead.fid_ms = ps_m.get("fid_ms")
                lead.speed_index = ps_m.get("speed_index")
                lead.pagespeed_opportunities = ps_m.get("opportunities")
                social = await score_social(html)
                lead.social_platforms = social.get("social_platforms")
                lead.social_score = social.get("social_score")
                lead.social_active = social.get("social_active")
        else:
            social = {"social_score": 0, "social_active": False, "social_platforms": {}}

    years = copyright_years(html) if html else []
    site_age_years = None
    if years:
        site_age_years = max(0, datetime.utcnow().year - min(years))

    smb_fit = assess_smb_fit(
        lead.business_name,
        html,
        {},
        features,
        pagespeed,
        scraped_meta,
        lead.review_count,
    )
    features["smb_fit"] = smb_fit

    lead.website_builder = features.get("builder")
    lead.features = features

    issues, critical, missing = build_issues(
        features,
        pagespeed,
        scraped_meta,
        lead.category,
    )
    if smb_fit.get("target_tier") == "likely_chain":
        issues = [
            {
                "severity": "low",
                "code": "likely_chain",
                "title": "Likely chain / national brand",
                "description": "Automated signals suggest this is not an ideal solo-dev client. Verify before outreach; lead score is reduced.",
                "impact": 0,
            },
            *issues,
        ]
    lead.issues = issues
    lead.critical_issues = critical
    lead.missing_features = missing

    rev, rev_desc = compute_revenue_opportunity(
        lead.category,
        lead.review_count,
        lead.google_rating,
        features,
        no_website,
        _parse_city(lead.address),
    )
    lead.revenue_opportunity_monthly = rev
    lead.revenue_opportunity_desc = rev_desc

    biz_dict = {
        "business_name": lead.business_name,
        "latitude": lead.latitude,
        "longitude": lead.longitude,
        "category": lead.category,
        "place_id": lead.place_id,
        "features": features,
        "google_rating": lead.google_rating,
    }
    comp = await asyncio.to_thread(
        find_competitors,
        settings.google_places_api_key,
        biz_dict,
    )
    lead.competitors = comp.get("competitors")
    lead.competitive_gaps = comp.get("competitive_gap")
    gap_count = len(lead.competitive_gaps or []) or (
        min(3, len(lead.competitors or [])) if lead.competitors else 0
    )

    scores = compute_scores(
        no_website=no_website,
        website_builder=lead.website_builder,
        revenue_monthly=rev or 0,
        features=features,
        google_rating=lead.google_rating,
        review_count=lead.review_count,
        category=lead.category,
        competitor_feature_gap_count=min(3, gap_count),
        pagespeed=pagespeed,
        social=social,
        site_age_years=site_age_years,
        has_errors=bool(scraped_meta.get("page_errors")),
        is_new_business=(lead.review_count or 0) < 50,
        smb_fit=smb_fit,
    )
    lead.opportunity_score = int(scores["opportunity_score"])
    lead.technical_debt_score = int(scores["technical_debt_score"])
    lead.urgency_score = int(scores["urgency_score"])
    raw_lead_score = float(scores["lead_score"])
    features["_score_pre_learning"] = raw_lead_score
    lead.lead_score = apply_pattern_multiplier(db, raw_lead_score, smb_fit, lead.website_builder)
    lead.features = features
    lead.seo_score = int(scores["seo_score"])
    lead.mobile_score = int(scores["mobile_score"])
    lead.content_score = int(scores["content_score"])
    lead.site_age_years = site_age_years

    # Screenshot diff
    if lead.desktop_screenshot_path and lead.last_screenshoted:
        # compare with previous file pattern - simplified: skip if first run
        pass
    lead.last_screenshoted = datetime.utcnow()

    smb_signals = str(smb_fit)[:2200]

    si_pre = features.get("site_intel") or {}
    if no_website:
        site_intel_line = (
            "No live page — prioritize 'no site' or listings-only positioning; skip stack commentary."
        )
    elif si_pre.get("archetype"):
        site_intel_line = (
            f"Archetype `{si_pre.get('archetype')}` · static_affinity={si_pre.get('static_affinity')} "
            f"(higher ≈ simpler brochure HTML) · spa_risk={si_pre.get('spa_risk')}. "
            "Match easy_wins and tech_simplicity_note to this shape; avoid enterprise replatform talk on brochure_static, "
            "avoid trivial CSS tweaks as the whole plan on app_like."
        )
    else:
        site_intel_line = "Page shape unknown — keep stack advice conservative."

    prompt = ANALYSIS_PROMPT.format(
        name=lead.business_name,
        category=lead.category or "",
        city=_parse_city(lead.address) or "",
        rating=lead.google_rating or "n/a",
        reviews=lead.review_count or 0,
        builder=lead.website_builder or "unknown",
        critical_issues=", ".join(critical[:6]) or "none listed",
        missing_features=", ".join(missing) or "none listed",
        opportunity_calc=rev,
        smb_signals=smb_signals,
        site_intel=site_intel_line,
    )

    try:
        data, model = await router.analyze(prompt, "full_analysis")
        lead.ai_model_used = model
        lead.ai_summary = data.get("summary")
        lead.ai_biggest_problem = data.get("biggest_problem")
        lead.ai_pitch = data.get("pitch_angle")
        lead.ai_recommended_service = data.get("recommended_service")
        lead.ai_estimated_value = data.get("estimated_value")
        lead.ai_revenue_opportunity = data.get("revenue_opportunity")
        lead.ai_urgency_reason = data.get("urgency_reason")
        features["ai_smb_intel"] = {
            "easy_wins": data.get("easy_wins") or [],
            "chain_verdict": data.get("chain_verdict"),
            "ideal_client_for_solo_dev": data.get("ideal_client_for_solo_dev"),
            "tech_simplicity_note": data.get("tech_simplicity_note"),
            "what_not_to_sell": data.get("what_not_to_sell"),
        }
        lead.features = features
    except Exception as e:
        logger.warning("AI analysis failed: %s", e)
        lead.ai_model_used = "none"
        lead.ai_summary = lead.revenue_opportunity_desc
        lead.ai_biggest_problem = (critical[0] if critical else "Website needs improvement")
        lead.ai_pitch = f"Open with local {lead.category or 'business'} relevance."
        lead.ai_recommended_service = "Website fixes"
        lead.ai_estimated_value = "$2,500–$5,000"
        lead.ai_revenue_opportunity = f"${rev}/mo"
        lead.ai_urgency_reason = "Competitors are capturing more online demand."

    pitch_prompt = PITCH_PROMPT.format(
        name=lead.business_name,
        category=lead.category or "",
        city=_parse_city(lead.address) or "",
        summary=lead.ai_summary or "",
        biggest_problem=lead.ai_biggest_problem or "",
        pitch_angle=lead.ai_pitch or "",
        revenue_note=lead.revenue_opportunity_desc or "",
    )
    try:
        pitch_json, _ = await router.analyze(pitch_prompt, "pitch")
        lead.email_pitch = (pitch_json.get("body") or "")[:8000]
    except Exception:
        lead.email_pitch = ""

    lead_dict = {
        "business_name": lead.business_name,
        "city": _parse_city(lead.address),
        "category": lead.category,
        "address": lead.address,
        "phone": lead.phone,
        "ai_biggest_problem": lead.ai_biggest_problem,
        "critical_issues": critical,
        "revenue_opportunity_monthly": lead.revenue_opportunity_monthly,
        "competitors": lead.competitors,
        "ai_estimated_value": lead.ai_estimated_value,
        "lead_score": lead.lead_score,
        "ai_pitch": lead.ai_pitch,
        "ai_recommended_service": lead.ai_recommended_service,
    }
    lead.call_script = generate_call_script(lead_dict)

    try:
        lead.audio_briefing_path = generate_audio_briefing(
            lead.id,
            {
                **lead_dict,
                "ai_pitch": lead.ai_pitch,
                "ai_recommended_service": lead.ai_recommended_service,
            },
        )
    except Exception as e:
        logger.warning("Audio: %s", e)

    lead.last_analyzed_at = datetime.utcnow()
    db.commit()


def apply_screenshot_diff_if_needed(
    lead: BusinessLead,
    previous_desktop_path: Optional[str],
) -> None:
    if not previous_desktop_path or not lead.desktop_screenshot_path:
        return
    diff = detect_changes(previous_desktop_path, lead.desktop_screenshot_path)
    lead.screenshot_change_pct = diff.get("change_percentage")
    if diff.get("status") == "major_change" and (diff.get("change_percentage") or 0) > 15:
        if lead.lead_score and lead.lead_score > 75:
            lead.site_improved = True
