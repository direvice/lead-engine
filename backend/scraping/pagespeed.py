"""Google PageSpeed Insights API."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

PS_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


async def run_pagespeed(url: str, api_key: str, strategy: str = "mobile") -> dict[str, Any]:
    if not api_key or not url.startswith("http"):
        return {}
    params = {"url": url, "strategy": strategy, "key": api_key}
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            r = await client.get(PS_URL, params=params)
            if r.status_code != 200:
                logger.warning("PageSpeed %s: %s", r.status_code, r.text[:300])
                return {}
            data = r.json()
        except Exception as e:
            logger.warning("PageSpeed error: %s", e)
            return {}

    lh = data.get("lighthouseResult", {})
    cats = lh.get("categories", {})
    perf = cats.get("performance", {})
    score_raw = perf.get("score")
    performance_score = int(round(float(score_raw) * 100)) if score_raw is not None else None

    audits = lh.get("audits", {})

    def _metric(name: str) -> Optional[float]:
        a = audits.get(name, {})
        return a.get("numericValue")

    lcp = _metric("largest-contentful-paint")
    fid = _metric("max-potential-fid") or _metric("total-blocking-time")
    cls = _metric("cumulative-layout-shift")
    fcp = _metric("first-contentful-paint")
    si = _metric("speed-index")

    opportunities = []
    for aid, aud in audits.items():
        if aud.get("score") is not None and aud.get("score", 1) < 1 and "opportunity" in (
            aud.get("details", {}) or {}
        ):
            opportunities.append(
                {
                    "id": aid,
                    "title": aud.get("title"),
                    "description": (aud.get("description") or "")[:500],
                }
            )
        if len(opportunities) >= 12:
            break

    diagnostics = []
    for aid, aud in list(audits.items())[:30]:
        if aud.get("scoreDisplayMode") == "informative" and aud.get("details"):
            diagnostics.append({"id": aid, "title": aud.get("title")})

    return {
        "performance_score": performance_score,
        "lcp_ms": int(lcp) if lcp else None,
        "fid_ms": int(fid) if fid else None,
        "cls_score": float(cls) if cls is not None else None,
        "fcp_ms": int(fcp) if fcp else None,
        "speed_index": int(si) if si else None,
        "opportunities": opportunities,
        "diagnostics": diagnostics[:15],
    }
