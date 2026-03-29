"""Yelp Fusion API discovery."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

YELP_SEARCH = "https://api.yelp.com/v3/businesses/search"
YELP_DETAIL = "https://api.yelp.com/v3/businesses/{id}"


async def yelp_search(
    api_key: str,
    location: str,
    term: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if not api_key:
        return []
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"location": location, "term": term, "limit": min(limit, 50)}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(YELP_SEARCH, headers=headers, params=params)
        if r.status_code != 200:
            logger.warning("Yelp search failed: %s %s", r.status_code, r.text[:200])
            return []
        data = r.json()
    businesses = data.get("businesses") or []
    out: list[dict[str, Any]] = []
    for b in businesses:
        bid = b.get("id")
        if not bid:
            continue
        loc = b.get("location") or {}
        addr_parts = [
            " ".join(loc.get("display_address") or []),
        ]
        address = addr_parts[0] if addr_parts else None
        cats = [c.get("title") for c in (b.get("categories") or []) if c.get("title")]
        website: Optional[str] = None
        phone = b.get("display_phone") or b.get("phone")
        out.append(
            {
                "place_id": f"yelp_{bid}",
                "business_name": b.get("name"),
                "address": address,
                "latitude": b.get("coordinates", {}).get("latitude"),
                "longitude": b.get("coordinates", {}).get("longitude"),
                "google_rating": b.get("rating"),
                "review_count": b.get("review_count"),
                "category": cats[0] if cats else "business",
                "types": cats,
                "business_status": "OPERATIONAL" if not b.get("is_closed") else "CLOSED",
                "website": website,
                "phone": phone,
                "source": "yelp",
                "source_ids": {"yelp": bid},
            }
        )
    async with httpx.AsyncClient(timeout=20.0) as client:
        for row in out:
            bid = row.get("source_ids", {}).get("yelp")
            if not bid:
                continue
            try:
                dr = await client.get(YELP_DETAIL.format(id=bid), headers=headers)
                if dr.status_code == 200:
                    detail = dr.json()
                    row["website"] = detail.get("url") or row.get("website")
            except Exception as e:
                logger.debug("Yelp detail %s: %s", bid, e)
    return [x for x in out if x.get("business_status") == "OPERATIONAL"]


async def discover_yelp_terms(
    api_key: str, location: str, terms: Optional[list[str]] = None
) -> list[dict[str, Any]]:
    terms = terms or [
        "restaurants",
        "retail",
        "beauty",
        "health",
        "automotive",
        "professional",
    ]
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for t in terms:
        batch = await yelp_search(api_key, location, t, limit=50)
        for b in batch:
            sid = b.get("source_ids", {}).get("yelp")
            if sid and sid not in seen:
                seen.add(sid)
                merged.append(b)
    return merged
