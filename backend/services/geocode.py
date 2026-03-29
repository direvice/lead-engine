"""Geocode free-form location to lat/lng.

Order: Google (if key) → Geoapify geocode (if GEOAPIFY_API_KEY) → Nominatim → Photon.
Nominatim policy: https://operations.osmfoundation.org/policies/nominatim/ — be polite (~1 req/s).
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
PHOTON_SEARCH = "https://photon.komoot.io/api/"
GEOAPIFY_GEOCODE = "https://api.geoapify.com/v1/geocode/search"
# Required by Nominatim; identify your app if you deploy publicly.
NOMINATIM_UA = "LeadEngine/1.0 (https://github.com/local-lead-research; contact: you@example.com)"
PHOTON_UA = NOMINATIM_UA


def geocode_google(api_key: str, location: str) -> Optional[Tuple[float, float]]:
    if not api_key or not location:
        return None
    try:
        import googlemaps

        client = googlemaps.Client(key=api_key)
        res = client.geocode(location)
        if not res:
            return None
        loc = res[0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    except Exception as e:
        logger.warning("Google geocode failed: %s", e)
        return None


def geocode_nominatim(location: str) -> Optional[Tuple[float, float]]:
    """Free OSM geocoding — no API key."""
    if not location or not location.strip():
        return None
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(
                NOMINATIM_SEARCH,
                params={
                    "q": location.strip(),
                    "format": "json",
                    "limit": 1,
                },
                headers={"User-Agent": NOMINATIM_UA},
            )
            if r.status_code != 200:
                logger.warning("Nominatim HTTP %s", r.status_code)
                return None
            data = r.json()
            if not data:
                return None
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.warning("Nominatim geocode failed: %s", e)
        return None


def geocode_photon(location: str) -> Optional[Tuple[float, float]]:
    """Komoot Photon (OSM-based) — no key; often works when Nominatim blocks datacenter IPs."""
    if not location or not location.strip():
        return None
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(
                PHOTON_SEARCH,
                params={"q": location.strip(), "limit": 1},
                headers={"User-Agent": PHOTON_UA, "Accept": "application/json"},
            )
            if r.status_code != 200:
                logger.warning("Photon HTTP %s", r.status_code)
                return None
            data = r.json()
            feats = data.get("features") or []
            if not feats:
                return None
            coords = feats[0].get("geometry", {}).get("coordinates")
            if not coords or len(coords) < 2:
                return None
            lon, lat = float(coords[0]), float(coords[1])
            return lat, lon
    except Exception as e:
        logger.warning("Photon geocode failed: %s", e)
        return None


def geocode_geoapify(api_key: str, location: str) -> Optional[Tuple[float, float]]:
    """Forward geocode via Geoapify (same key as Places)."""
    if not api_key or not location or not location.strip():
        return None
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(
                GEOAPIFY_GEOCODE,
                params={"text": location.strip(), "limit": 1, "apiKey": api_key.strip()},
            )
            if r.status_code != 200:
                logger.warning("Geoapify geocode HTTP %s", r.status_code)
                return None
            feats = (r.json().get("features") or [])[:1]
            if not feats:
                return None
            coords = feats[0].get("geometry", {}).get("coordinates")
            if not coords or len(coords) < 2:
                return None
            lon, lat = float(coords[0]), float(coords[1])
            return lat, lon
    except Exception as e:
        logger.warning("Geoapify geocode failed: %s", e)
        return None


def resolve_coordinates(
    location: str,
    google_api_key: str = "",
    geoapify_api_key: str = "",
) -> Optional[Tuple[float, float]]:
    """Google first, then Geoapify, then Nominatim, then Photon."""
    if google_api_key:
        c = geocode_google(google_api_key, location)
        if c:
            return c
        logger.info("Google geocode empty; trying Geoapify")
    if geoapify_api_key:
        c = geocode_geoapify(geoapify_api_key, location)
        if c:
            return c
        logger.info("Geoapify geocode empty; trying Nominatim")
    c = geocode_nominatim(location)
    if c:
        return c
    logger.info("Nominatim failed; trying Photon")
    return geocode_photon(location)


# Backwards-compatible: Google key only (no Geoapify)
def geocode(api_key: str, location: str) -> Optional[Tuple[float, float]]:
    return resolve_coordinates(location, api_key or "", "")
