"""Yellowpages.com lightweight HTML discovery (best-effort)."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

UA = "Mozilla/5.0 (compatible; FoxValleyDigital-LeadBot/1.0; +https://example.com)"


async def search_yellowpages(
    location: str,
    search_term: str,
    max_results: int = 30,
) -> list[dict[str, Any]]:
    url = f"https://www.yellowpages.com/search?search_terms={quote_plus(search_term)}&geo_location_terms={quote_plus(location)}"
    headers = {"User-Agent": UA}
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
        try:
            r = await client.get(url, headers=headers)
        except Exception as e:
            logger.warning("YP request failed: %s", e)
            return []
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "lxml")
    results: list[dict[str, Any]] = []
    for idx, vcard in enumerate(soup.select(".result, .search-result")):
        if len(results) >= max_results:
            break
        name_el = vcard.select_one(".business-name, .n")
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        phone_el = vcard.select_one(".phones, .phone")
        phone = phone_el.get_text(strip=True) if phone_el else None
        street = vcard.select_one(".street")
        locality = vcard.select_one(".locality")
        addr = " ".join(
            filter(None, [street.get_text(strip=True) if street else None, locality.get_text(strip=True) if locality else None])
        )
        link = name_el.get("href") if name_el.name == "a" else None
        if not link and name_el.find_parent("a"):
            link = name_el.find_parent("a").get("href")
        website = None
        if link and link.startswith("http"):
            website = link
        bid = re.sub(r"\W+", "_", name)[:80] + f"_{idx}"
        results.append(
            {
                "place_id": f"yp_{bid}",
                "business_name": name,
                "address": addr or None,
                "latitude": None,
                "longitude": None,
                "google_rating": None,
                "review_count": None,
                "category": search_term,
                "types": [search_term],
                "business_status": "OPERATIONAL",
                "website": website,
                "phone": phone,
                "source": "yellowpages",
                "source_ids": {"yellowpages": bid},
            }
        )
    return results
