"""Google Places nearby search — multiple categories."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import googlemaps

logger = logging.getLogger(__name__)

PLACE_TYPES: list[str] = [
    "restaurant",
    "cafe",
    "bar",
    "bakery",
    "meal_takeaway",
    "meal_delivery",
    "clothing_store",
    "shoe_store",
    "jewelry_store",
    "book_store",
    "furniture_store",
    "home_goods_store",
    "hardware_store",
    "pet_store",
    "florist",
    "store",
    "hair_care",
    "beauty_salon",
    "spa",
    "gym",
    "dentist",
    "doctor",
    "physiotherapist",
    "lawyer",
    "accounting",
    "real_estate_agency",
    "insurance_agency",
    "car_dealer",
    "car_repair",
    "car_wash",
    "plumber",
    "electrician",
    "general_contractor",
    "painter",
    "locksmith",
    "travel_agency",
    "moving_company",
    "veterinary_care",
]


def _normalize_business(place: dict[str, Any], source: str = "google") -> dict[str, Any]:
    pid = place.get("place_id")
    name = place.get("name") or "Unknown"
    loc = place.get("geometry", {}).get("location") or {}
    lat = loc.get("lat")
    lng = loc.get("lng")
    addr = place.get("formatted_address") or place.get("vicinity") or ""
    types = place.get("types") or []
    rating = place.get("rating")
    reviews = place.get("user_ratings_total")
    status = place.get("business_status") or place.get("opening_hours", {}).get(
        "open_now"
    )
    bs = place.get("business_status")
    if isinstance(bs, str):
        business_status = bs
    else:
        business_status = "OPERATIONAL"
    return {
        "place_id": pid,
        "business_name": name,
        "address": addr,
        "latitude": lat,
        "longitude": lng,
        "google_rating": rating,
        "review_count": reviews,
        "category": types[0] if types else None,
        "types": types,
        "business_status": business_status,
        "website": None,
        "phone": None,
        "source": source,
        "source_ids": {"google": pid},
        "raw_types": types,
    }


def discover_google_places(
    api_key: str,
    lat: float,
    lng: float,
    radius_meters: int = 15000,
    max_per_type: int = 60,
) -> list[dict[str, Any]]:
    if not api_key:
        return []
    client = googlemaps.Client(key=api_key)
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    for ptype in PLACE_TYPES:
        token: Optional[str] = None
        count = 0
        while count < max_per_type:
            try:
                resp = client.places_nearby(
                    location=(lat, lng),
                    radius=radius_meters,
                    type=ptype,
                    page_token=token,
                )
            except Exception as e:
                logger.warning("Places nearby error type=%s: %s", ptype, e)
                break
            for r in resp.get("results", []):
                pid = r.get("place_id")
                if not pid or pid in seen:
                    continue
                if r.get("business_status") and r["business_status"] != "OPERATIONAL":
                    continue
                seen.add(pid)
                out.append(_normalize_business(r))
                count += 1
                if count >= max_per_type:
                    break
            token = resp.get("next_page_token")
            if not token:
                break
            time.sleep(2)

    # Enrich with details (website, phone) — batched lightly
    enriched: list[dict[str, Any]] = []
    for b in out:
        pid = b.get("place_id")
        if not pid:
            enriched.append(b)
            continue
        try:
            det = client.place(place_id=pid, fields=["website", "formatted_phone_number"])
            res = det.get("result", {})
            b["website"] = res.get("website")
            b["phone"] = res.get("formatted_phone_number")
        except Exception as e:
            logger.debug("Place details %s: %s", pid, e)
        enriched.append(b)

    return enriched
