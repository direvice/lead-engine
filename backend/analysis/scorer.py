"""Lead scoring — opportunity, technical debt, urgency, final."""

from __future__ import annotations

from typing import Any


def _category_bucket(category: str | None) -> str:
    c = (category or "").lower()
    if any(x in c for x in ("restaurant", "food", "cafe", "bar", "bakery", "meal")):
        return "restaurant"
    if any(x in c for x in ("store", "retail", "shop", "clothing", "gift")):
        return "retail"
    return "service"


def _pagespeed_penalty(pagespeed: dict[str, Any]) -> int:
    s = pagespeed.get("performance_score")
    if s is None:
        return 15
    if s >= 90:
        return 0
    if s >= 70:
        return 10
    if s >= 50:
        return 25
    return 45


def compute_scores(
    *,
    no_website: bool,
    website_builder: str | None,
    revenue_monthly: int,
    features: dict[str, Any],
    google_rating: float | None,
    review_count: int | None,
    category: str | None,
    competitor_feature_gap_count: int,
    pagespeed: dict[str, Any],
    social: dict[str, Any],
    site_age_years: float | None,
    has_errors: bool,
    is_new_business: bool,
) -> dict[str, float]:
    opportunity = 0.0

    if no_website:
        opportunity = 95.0
    else:
        opportunity = 20.0
        if website_builder:
            opportunity += 28.0
        if revenue_monthly > 5000:
            opportunity += 25.0
        elif revenue_monthly >= 2000:
            opportunity += 18.0
        elif revenue_monthly > 0:
            opportunity += 10.0

        bucket = _category_bucket(category)
        if bucket == "restaurant" and not features.get("has_online_ordering"):
            opportunity += 22.0
        if bucket == "retail" and not features.get("has_ecommerce"):
            opportunity += 22.0
        if bucket == "service" and not features.get("has_booking"):
            opportunity += 18.0

        gr = google_rating or 0
        rc = review_count or 0
        bad_site = pagespeed.get("performance_score") is None or (
            pagespeed.get("performance_score") is not None
            and pagespeed.get("performance_score", 100) < 70
        )
        if gr >= 4.5 and bad_site:
            opportunity += 20.0
        if rc > 100 and bad_site:
            opportunity += 15.0

        opportunity += min(36, competitor_feature_gap_count * 12)

        if not features.get("has_analytics"):
            opportunity += 8.0
        if not features.get("has_blog"):
            opportunity += 6.0

        if (social.get("social_score") or 0) >= 25 and bad_site:
            opportunity += 15.0

    opportunity = min(100.0, opportunity)

    tech = _pagespeed_penalty(pagespeed)
    if features.get("duplicate_text_bug"):
        tech += 15
    if features.get("has_horizontal_scroll"):
        tech += 8
    tech = min(100.0, float(tech))

    urgency = 0.0
    if site_age_years is not None and site_age_years >= 2:
        urgency += 20.0
    if has_errors:
        urgency += 30.0
    if is_new_business:
        urgency += 15.0
    urgency = min(100.0, urgency)

    rating_bonus = 15.0 if (google_rating or 0) >= 4.0 else 0.0

    final = (
        opportunity * 0.40
        + tech * 0.25
        + urgency * 0.20
        + rating_bonus * 0.15
    )
    final = min(100.0, max(0.0, final))

    # Sub-scores for UI rings (derived)
    seo = max(0, 100 - (20 if not features.get("has_blog") else 0) - tech * 0.3)
    mobile = max(
        0,
        100
        - (30 if features.get("has_horizontal_scroll") else 0)
        - _pagespeed_penalty(pagespeed),
    )
    content = max(0, 100 - (25 if features.get("duplicate_text_bug") else 0))

    return {
        "opportunity_score": round(opportunity, 1),
        "technical_debt_score": round(tech, 1),
        "urgency_score": round(urgency, 1),
        "lead_score": round(final, 1),
        "seo_score": round(min(100, seo), 1),
        "mobile_score": round(min(100, mobile), 1),
        "content_score": round(min(100, content), 1),
    }
