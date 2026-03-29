"""Geoapify Places API — optional Google Places replacement (free tier: https://www.geoapify.com/)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GEOAPIFY_PLACES = "https://api.geoapify.com/v2/places"

# Batched Geoapify categories (~1 request per batch). See https://apidocs.geoapify.com/docs/places/
_CATEGORY_BATCHES: list[str] = [
    "catering.restaurant,catering.cafe,catering.bar,catering.bakery,catering.fast_food",
    "commercial.clothing,commercial.shoes,commercial.jewelry,commercial.books,commercial.furniture",
    "commercial.houseware,commercial.do_it_yourself,commercial.gift,commercial.department_store",
    "pet,service.beauty,leisure.spa,sport.fitness",
    "healthcare.dentist,healthcare.doctor,healthcare.physiotherapist",
    "service.lawyer,service.accountant,service.estate_agent,service.insurance",
    "commercial.car,service.car_repair,service.car_wash",
    "craft.plumber,craft.electrician,craft.carpenter,craft.painter,service.locksmith",
    "service.travel_agency,service.moving_company,pet.veterinary",
]


def _normalize_feature(f: dict[str, Any]) -> dict[str, Any] | None:
    props = f.get("properties") or {}
    geom = f.get("geometry") or {}
    coords = geom.get("coordinates")
    if not coords or len(coords) < 2:
        return None
    lon, lat = float(coords[0]), float(coords[1])
    name = props.get("name")
    if not name:
        return None
    cats = props.get("categories") or []
    cat0 = cats[0] if cats else "business"
    addr_parts = [
        " ".join(
            filter(
                None,
                [
                    props.get("housenumber"),
                    props.get("street"),
                ],
            )
        ).strip(),
        props.get("city"),
        props.get("state"),
        props.get("postcode"),
    ]
    address = ", ".join(p for p in addr_parts if p) or None
    pid = props.get("place_id")
    if not pid:
        ds = props.get("datasource")
        if isinstance(ds, dict):
            raw = ds.get("raw")
            if isinstance(raw, dict):
                pid = raw.get("osm_id") or raw.get("id")
    sid = f"geoapify_{pid}" if pid else f"geoapify_{lat:.5f}_{lon:.5f}_{abs(hash(name)) % 10_000_000}"
    return {
        "place_id": sid,
        "business_name": name,
        "address": address,
        "latitude": lat,
        "longitude": lon,
        "google_rating": None,
        "review_count": None,
        "category": cat0,
        "types": list(cats) if isinstance(cats, list) else [str(cats)],
        "business_status": "OPERATIONAL",
        "website": props.get("website") or None,
        "phone": props.get("phone") or props.get("formatted") or None,
        "source": "geoapify",
        "source_ids": {"geoapify": str(pid or sid)},
    }


async def discover_geoapify_places(
    api_key: str,
    lat: float,
    lng: float,
    radius_meters: int = 15000,
    limit_per_batch: int = 80,
) -> list[dict[str, Any]]:
    if not api_key or not api_key.strip():
        return []
    r_m = max(100, min(radius_meters, 50_000))
    # Geoapify circle filter: lon,lat,radiusMeters
    filt = f"circle:{lng},{lat},{r_m}"
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=45.0) as client:
        for cats in _CATEGORY_BATCHES:
            try:
                r = await client.get(
                    GEOAPIFY_PLACES,
                    params={
                        "filter": filt,
                        "categories": cats,
                        "limit": min(limit_per_batch, 120),
                        "apiKey": api_key.strip(),
                    },
                )
            except Exception as e:
                logger.warning("Geoapify request failed: %s", e)
                continue
            if r.status_code != 200:
                logger.warning("Geoapify HTTP %s: %s", r.status_code, r.text[:200])
                continue
            data = r.json()
            for feat in data.get("features") or []:
                row = _normalize_feature(feat)
                if not row:
                    continue
                key = row["place_id"]
                if key in seen:
                    continue
                seen.add(key)
                out.append(row)
    return out
