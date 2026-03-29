"""Facebook Graph — optional Page search when access token is set."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GRAPH = "https://graph.facebook.com/v18.0/pages/search"


async def search_facebook_pages(
    access_token: str,
    q: str,
    center: tuple[float, float] | None = None,
    distance_m: int = 25000,
    limit: int = 25,
) -> list[dict[str, Any]]:
    if not access_token:
        return []
    params: dict[str, Any] = {
        "access_token": access_token,
        "q": q,
        "fields": "name,location,phone,website_link,link",
        "limit": limit,
    }
    if center:
        params["center"] = f"{center[0]},{center[1]}"
        params["distance"] = distance_m
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(GRAPH, params=params)
        if r.status_code != 200:
            logger.warning("Facebook search failed: %s", r.text[:200])
            return []
        data = r.json()
    out: list[dict[str, Any]] = []
    for p in data.get("data", []):
        pid = p.get("id")
        loc = p.get("location") or {}
        addr = ", ".join(
            filter(
                None,
                [
                    loc.get("street"),
                    loc.get("city"),
                    loc.get("state"),
                    loc.get("zip"),
                ],
            )
        )
        out.append(
            {
                "place_id": f"fb_{pid}",
                "business_name": p.get("name"),
                "address": addr or None,
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "google_rating": None,
                "review_count": None,
                "category": "facebook_page",
                "types": ["facebook_page"],
                "business_status": "OPERATIONAL",
                "website": p.get("website_link") or p.get("link"),
                "phone": p.get("phone"),
                "source": "facebook",
                "source_ids": {"facebook": pid},
            }
        )
    return out
