"""Lightweight social signals from homepage links (no heavy IG/FB scraping)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

import httpx
from bs4 import BeautifulSoup


def extract_social_links(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    platforms: dict[str, Any] = {}
    for a in soup.find_all("a", href=True):
        h = a["href"].lower()
        if "facebook.com" in h and "facebook" not in platforms:
            platforms["facebook"] = {"url": a["href"]}
        if "instagram.com" in h and "instagram" not in platforms:
            platforms["instagram"] = {"url": a["href"]}
    return platforms


async def _fetch_meta_dates(url: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            r = await client.get(
                url,
                headers={"User-Agent": "FoxValleyDigital-LeadBot/1.0"},
            )
            if r.status_code != 200:
                return out
            text = r.text
            # og:updated_time
            m = re.search(
                r'property=["\']og:updated_time["\']\s+content=["\']([^"\']+)',
                text,
                re.I,
            )
            if m:
                out["last_signal"] = m.group(1)
    except Exception:
        pass
    return out


async def score_social(html: str) -> dict[str, Any]:
    platforms = extract_social_links(html)
    score = 0
    active = False
    now = datetime.utcnow()

    for name, meta in platforms.items():
        url = meta.get("url")
        if not url:
            continue
        extra = await _fetch_meta_dates(url)
        meta.update(extra)
        if extra.get("last_signal"):
            try:
                dt = datetime.fromisoformat(extra["last_signal"].replace("Z", "+00:00"))
                if now - dt.replace(tzinfo=None) < timedelta(days=30):
                    score += 30
                    active = True
                elif now - dt.replace(tzinfo=None) > timedelta(days=90):
                    score -= 20
            except Exception:
                score += 10
        else:
            score += 10

    if len(platforms) >= 2:
        score += 20
    return {
        "social_platforms": platforms,
        "social_score": max(-40, min(100, score)),
        "social_active": active or len(platforms) > 0,
    }
