"""OpenStreetMap / Overpass discovery (free, no key)."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import overpy

logger = logging.getLogger(__name__)


def _run_overpass(lat: float, lon: float, radius_meters: int) -> overpy.Result:
    api = overpy.Overpass()
    query = f"""
    [out:json][timeout:60];
    (
      node["shop"]["name"](around:{radius_meters},{lat},{lon});
      node["amenity"~"restaurant|cafe|bar|fast_food|dentist|doctors|pharmacy|bank"]["name"](around:{radius_meters},{lat},{lon});
      node["office"~"lawyer|accountant|insurance|estate_agent"]["name"](around:{radius_meters},{lat},{lon});
    );
    out body;
    """
    return api.query(query)


def _tags_to_business(node: Any) -> dict[str, Any]:
    tags = node.tags or {}
    name = tags.get("name")
    if not name:
        return {}
    website = tags.get("website") or tags.get("contact:website") or ""
    phone = tags.get("phone") or tags.get("contact:phone") or ""
    addr = " ".join(
        filter(
            None,
            [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:city"),
                tags.get("addr:state"),
                tags.get("addr:postcode"),
            ],
        )
    )
    cat = tags.get("shop") or tags.get("amenity") or tags.get("office") or "business"
    return {
        "place_id": f"osm_{node.id}",
        "business_name": name,
        "address": addr or None,
        "latitude": float(node.lat),
        "longitude": float(node.lon),
        "google_rating": None,
        "review_count": None,
        "category": cat,
        "types": [cat],
        "business_status": "OPERATIONAL",
        "website": website or None,
        "phone": _normalize_phone(phone) if phone else None,
        "source": "osm",
        "source_ids": {"osm": str(node.id)},
    }


def _normalize_phone(p: str) -> str:
    return re.sub(r"[^\d+]", "", p) or p


async def search_osm(lat: float, lon: float, radius_meters: int = 5000) -> list[dict[str, Any]]:
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, lambda: _run_overpass(lat, lon, radius_meters)
        )
    except Exception as e:
        logger.warning("OSM Overpass error: %s", e)
        return []

    out: list[dict[str, Any]] = []
    for node in result.nodes:
        b = _tags_to_business(node)
        if b:
            out.append(b)
    return out
