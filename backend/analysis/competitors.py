"""Competitor discovery via Google Places."""

from __future__ import annotations

import logging
from typing import Any, Optional

import googlemaps

logger = logging.getLogger(__name__)


def _popularity(rating: float | None, reviews: int | None) -> float:
    r = rating or 0
    n = reviews or 0
    return r * max(n, 1) ** 0.5


def find_competitors(
    api_key: str,
    business: dict[str, Any],
    radius_meters: int = 8000,
    top_n: int = 3,
) -> dict[str, Any]:
    if not api_key:
        return {"competitors": [], "competitive_gap": []}
    lat = business.get("latitude")
    lng = business.get("longitude")
    if lat is None or lng is None:
        return {"competitors": [], "competitive_gap": []}

    keyword = business.get("category") or business.get("business_name") or "business"
    if isinstance(keyword, list):
        keyword = keyword[0] if keyword else "business"

    client = googlemaps.Client(key=api_key)
    try:
        resp = client.places_nearby(
            location=(lat, lng),
            radius=radius_meters,
            keyword=str(keyword)[:80],
        )
    except Exception as e:
        logger.warning("Competitor search failed: %s", e)
        return {"competitors": [], "competitive_gap": []}

    self_name = (business.get("business_name") or "").lower()
    cands: list[dict[str, Any]] = []
    for r in resp.get("results", []):
        if (r.get("name") or "").lower() == self_name:
            continue
        if r.get("place_id") == business.get("place_id"):
            continue
        cands.append(r)

    cands.sort(
        key=lambda x: _popularity(x.get("rating"), x.get("user_ratings_total")),
        reverse=True,
    )
    top = cands[:top_n]

    competitors: list[dict[str, Any]] = []
    for t in top:
        competitors.append(
            {
                "name": t.get("name"),
                "rating": t.get("rating"),
                "review_count": t.get("user_ratings_total"),
                "has_online_ordering": None,
                "has_booking": None,
                "website_score": None,
                "website_builder": None,
                "place_id": t.get("place_id"),
            }
        )

    gaps: list[str] = []
    lead_order = business.get("features", {}).get("has_online_ordering")
    if lead_order is False and len(competitors) >= 2:
        gaps.append("Multiple nearby competitors may already capture online orders or visibility.")
    if (business.get("google_rating") or 0) < 4.3 and competitors:
        top_r = competitors[0].get("rating") or 0
        if top_r - (business.get("google_rating") or 0) >= 0.4:
            gaps.append(
                f"Top competitor {competitors[0].get('name')} shows stronger ratings — "
                "site + reviews workflow may be a gap."
            )

    return {"competitors": competitors, "competitive_gap": gaps}
