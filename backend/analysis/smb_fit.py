"""Score how good a lead is for a solo/small-shop web helper: local SMB, simple site, easy fixes — not national chains."""

from __future__ import annotations

import re
from typing import Any

# Names / fragments that strongly suggest corporate / franchise (deprioritize).
_CHAIN_FRAGMENTS: tuple[str, ...] = (
    "starbucks",
    "mcdonald",
    "subway",
    "wendy",
    "burger king",
    "taco bell",
    "chipotle",
    "panera",
    "dunkin",
    "chick-fil",
    "kfc",
    "pizza hut",
    "domino's",
    "dominos",
    "applebee",
    "olive garden",
    "red lobster",
    "texas roadhouse",
    "outback",
    "buffalo wild",
    "ihop",
    "denny's",
    "cracker barrel",
    "target",
    "walmart",
    "wal-mart",
    "home depot",
    "lowe's",
    "lowes",
    "cvs ",
    "cvs pharmacy",
    "walgreens",
    "rite aid",
    "best buy",
    "costco",
    "sam's club",
    "whole foods",
    "trader joe",
    "7-eleven",
    "speedway",
    "shell ",
    " bp ",
    "exxon",
    "marriott",
    "hilton",
    "holiday inn",
    "hyatt",
    "hampton inn",
    "la quinta",
    "motel 6",
    "spectrum",
    "verizon",
    "at&t",
    "t-mobile",
    "sprint ",
    "bank of america",
    "chase bank",
    "wells fargo",
    "u.s. bank",
    "pnc bank",
    "capital one",
    "enterprise rent",
    "hertz",
    "avis",
    "fedex",
    "ups store",
    "the ups store",
    "post office",
    "usps",
    "dollar general",
    "dollar tree",
    "family dollar",
    "ross ",
    "marshalls",
    "tj maxx",
    "kohl's",
    "petco",
    "petsmart",
    "gamestop",
    "staples",
    "office depot",
)


def _norm_name(name: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def chain_likelihood_from_name(business_name: str | None) -> int:
    n = _norm_name(business_name)
    if not n:
        return 0
    for frag in _CHAIN_FRAGMENTS:
        if frag in n:
            return 95
    # "X #1234" franchise numbering
    if re.search(r"\b#\s*\d{3,5}\b", business_name or ""):
        return 55
    return 0


def chain_signals_from_html(html: str) -> tuple[int, list[str]]:
    """Return (0-100 bump to chain score, reasons)."""
    if not html:
        return 0, []
    low = html.lower()
    reasons: list[str] = []
    bump = 0
    # Store locator / hundreds of locations language
    if re.search(r"\b\d{3,}\s+locations\b", low) or "find a location" in low and "near you" in low:
        bump += 40
        reasons.append("Nationwide location-finder language")
    if "sameas" in low and "wikipedia.org" in low:
        bump += 25
        reasons.append("Large-brand structured data (Wikipedia sameAs)")
    if low.count("location") > 40 and "all locations" in low:
        bump += 20
        reasons.append("Heavy multi-location copy")
    return min(100, bump), reasons


def simplicity_score(signals: dict[str, Any]) -> tuple[int, list[str]]:
    """Higher = simpler / more brochure-style site (good for quick wins)."""
    score = 50
    notes: list[str] = []
    hlen = signals.get("html_char_count") or 0
    if hlen and hlen < 45_000:
        score += 15
        notes.append("Modest page size (not a giant app)")
    elif hlen and hlen > 350_000:
        score -= 20
        notes.append("Very large HTML (complex build)")

    ext_scripts = signals.get("external_script_count") or 0
    if ext_scripts < 12:
        score += 10
        notes.append("Fewer third-party scripts")
    elif ext_scripts > 35:
        score -= 15
        notes.append("Many third-party scripts (harder quick wins)")

    if signals.get("has_viewport_meta"):
        score += 5
    else:
        score -= 5
        notes.append("Missing viewport meta (common easy fix)")

    builder = (signals.get("builder") or "").lower()
    if builder in ("wix", "weebly", "squarespace", "godaddy", "jimdo", "duda"):
        score += 12
        notes.append(f"Known builder ({signals.get('builder')}) — template-level fixes")
    if builder in ("shopify", "bigcommerce"):
        score -= 5

    internal = signals.get("internal_link_count") or 0
    if internal < 25:
        score += 8
        notes.append("Small link graph — likely brochure site")
    elif internal > 120:
        score -= 10

    return max(0, min(100, score)), notes


def fixability_score(
    features: dict[str, Any],
    pagespeed: dict[str, Any],
    scraped: dict[str, Any],
) -> tuple[int, list[str]]:
    """Higher = issues are mostly small / explainable wins."""
    score = 45
    notes: list[str] = []
    if features.get("duplicate_text_bug"):
        score += 18
        notes.append("Duplicate text bug — often a quick CSS/template fix")
    if scraped.get("has_horizontal_scroll"):
        score += 12
        notes.append("Horizontal scroll — usually responsive CSS")
    perf = pagespeed.get("performance_score")
    if perf is not None and perf < 60:
        score += 14
        notes.append("Low PageSpeed — images/fonts often move the needle fast")
    if not features.get("has_analytics"):
        score += 8
        notes.append("No analytics — simple GA/GTM install is a clear deliverable")
    if not features.get("has_blog"):
        score += 5
    if scraped.get("page_errors"):
        score += 10
        notes.append("Console errors — targeted JS fixes")
    return max(0, min(100, score)), notes


def assess_smb_fit(
    business_name: str | None,
    html: str,
    signals: dict[str, Any],
    features: dict[str, Any],
    pagespeed: dict[str, Any],
    scraped: dict[str, Any],
    review_count: int | None,
) -> dict[str, Any]:
    """
    Returns blob stored on lead.features['smb_fit'].
    target_tier: ideal_smb | borderline | likely_chain
    """
    name_chain = chain_likelihood_from_name(business_name)
    html_bump, html_reasons = chain_signals_from_html(html)
    chain_score = min(100, max(name_chain, int(html_bump * 0.7 + name_chain * 0.3)))

    # Huge review volume often = flagship / chain listing
    rc = review_count or 0
    if rc > 2500:
        chain_score = min(100, chain_score + 25)
        html_reasons.append("Very high review count (often national brand listing)")

    sim, sim_notes = simplicity_score({**features, **signals})
    fix, fix_notes = fixability_score(features, pagespeed, scraped)

    # Ideal = low chain, decent simplicity & fixability
    if chain_score >= 75:
        tier = "likely_chain"
    elif chain_score >= 45:
        tier = "borderline"
    else:
        tier = "ideal_smb"

    smb_fit_index = max(
        0,
        min(
            100,
            int(
                (100 - chain_score) * 0.45
                + sim * 0.30
                + fix * 0.25
            ),
        ),
    )

    return {
        "target_tier": tier,
        "chain_likelihood": chain_score,
        "simplicity_score": sim,
        "fixability_score": fix,
        "smb_fit_index": smb_fit_index,
        "reasons": list(
            dict.fromkeys(
                html_reasons + sim_notes + fix_notes
            )
        )[:12],
    }
