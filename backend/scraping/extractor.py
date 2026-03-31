"""HTML parsing — builders, features, duplicate text."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString

# Strong signals the first HTML payload is a JS-heavy SPA / framework shell (not a classic brochure site).
_SPA_FRAMEWORK_MARKERS: tuple[str, ...] = (
    "__next_data__",
    "__next_f.push",
    "data-reactroot",
    "data-react-helmet",
    "react-dom.production",
    "react-dom@",
    "_nuxt",
    "__nuxt__",
    "ng-version",
    "zone.js",
    "sveltekit",
    "sapper",
    "___gatsby",
    "gatsby-script",
    "webpackjsonp",
    "vite-plugin",
    "single-page application",
    "ember.js",
    "stimulus.min.js",
)

BUILDER_SIGNATURES: dict[str, list[str]] = {
    "Wix": ["wixstatic.com", "wix.com", "_wix_"],
    "GoDaddy": ["wsimg.com", "godaddy.com/websites", "secureserver.net"],
    "Squarespace": ["squarespace.com", "sqsp.net", "static1.squarespace.com"],
    "WordPress": ["/wp-content/", "/wp-includes/", "wp-json", "wordpress"],
    "Weebly": ["weebly.com", "weeblycloud.com"],
    "Shopify": ["cdn.shopify.com", "myshopify.com"],
    "Webflow": ["webflow.com", "data-wf-page"],
    "Square": ["square-site", "squareup.com"],
    "Jimdo": ["jimdo.com", "jimdosite.com"],
    "Duda": ["duda.co", "multiscreensite.com"],
    "BigCommerce": ["bigcommerce.com", "bcapp.dev"],
    "Wix ADI": ["wix.com/velo"],
}


def detect_builder(html: str) -> str | None:
    low = html.lower()
    for name, sigs in BUILDER_SIGNATURES.items():
        if any(s in low for s in sigs):
            return name
    return None


def infer_site_intel(
    *,
    low_html: str,
    external_script_count: int,
    html_char_count: int,
    internal_link_count: int,
    builder: str | None,
) -> dict[str, Any]:
    """
    Classify the first-page HTML as brochure-like (easy refit) vs app-like (heavy client JS).
    Used for ranking and autopilot queues — heuristics only, not ground truth.
    """
    hits = sum(1 for m in _SPA_FRAMEWORK_MARKERS if m in low_html)
    spa_risk = min(
        100.0,
        float(hits * 18 + max(0, external_script_count - 8) * 2.2),
    )
    if external_script_count >= 22:
        spa_risk = min(100.0, spa_risk + 12.0)

    brochure_boost = 0.0
    b = (builder or "").lower()
    if any(x in b for x in ("wix", "squarespace", "weebly", "jimdo", "godaddy", "duda")):
        brochure_boost += 28.0
    if internal_link_count >= 6 and html_char_count >= 3500:
        brochure_boost += 12.0
    if external_script_count <= 9:
        brochure_boost += 14.0

    static_affinity = max(0.0, min(100.0, 46.0 + brochure_boost - spa_risk * 0.55))

    # One strong framework marker (e.g. Next payload) is enough to treat as app shell.
    if spa_risk >= 58 or hits >= 2 or (hits >= 1 and spa_risk >= 14):
        archetype = "app_like"
    elif static_affinity >= 58 and spa_risk < 38:
        archetype = "brochure_static"
    else:
        archetype = "mixed"

    return {
        "archetype": archetype,
        "static_affinity": round(static_affinity, 1),
        "spa_risk": round(spa_risk, 1),
        "spa_marker_hits": hits,
    }


def extract_text_and_features(html: str, page_url: str | None = None) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    raw_text = soup.get_text(" ", strip=True).lower()
    low_html = html.lower()

    base_host = ""
    if page_url:
        try:
            base_host = (urlparse(page_url).hostname or "").lower()
        except Exception:
            base_host = ""

    scripts = soup.find_all("script", src=True)
    external_script_count = len(scripts)
    viewport = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
    has_viewport_meta = viewport is not None

    internal_link_count = 0
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        if href.startswith("/") or (base_host and base_host in href.lower()):
            internal_link_count += 1

    html_char_count = len(html)

    # Duplicate text nodes > 40 chars, count >= 3
    text_chunks: list[str] = []
    for el in soup.find_all(string=True):
        if isinstance(el, NavigableString) and el.parent and el.parent.name not in (
            "script",
            "style",
        ):
            t = str(el).strip()
            if len(t) > 40:
                text_chunks.append(t)
    counts: dict[str, int] = {}
    for t in text_chunks:
        counts[t] = counts.get(t, 0) + 1
    duplicate_text_bug = any(c >= 3 for c in counts.values())

    # Ordering
    order_iframes = [
        "doordash.com",
        "grubhub.com",
        "ubereats.com",
        "toasttab.com",
        "olo.com",
        "orderingapp.com",
        "slice.is",
        "bopple.com",
    ]
    order_links = ["/order", "/online-ordering", "doordash.com", "grubhub.com", "ubereats.com"]
    order_phrases = [
        "order online",
        "order now",
        "order for delivery",
        "order for pickup",
        "start order",
    ]
    has_ordering = any(x in low_html for x in order_iframes + order_links) or any(
        p in raw_text for p in order_phrases
    )

    booking_iframes = [
        "calendly.com",
        "acuityscheduling.com",
        "opentable.com",
        "yelp.com/reservations",
        "booksy.com",
        "mindbodyonline.com",
        "vagaro.com",
        "schedulicity.com",
        "squareup.com/appointments",
    ]
    booking_phrases = [
        "book appointment",
        "schedule appointment",
        "reserve a table",
        "book online",
        "make a reservation",
    ]
    has_booking = any(x in low_html for x in booking_iframes) or any(
        p in raw_text for p in booking_phrases
    )

    ecommerce = (
        "add to cart" in raw_text
        or "buy now" in raw_text
        or "add-to-cart" in low_html
        or "woocommerce" in low_html
        or ("shopify" in low_html and "cart" in raw_text)
    )

    live_chat_scripts = [
        "intercom.io",
        "drift.com",
        "tidio.com",
        "livechat.com",
        "freshdesk.com",
        "zendesk.com",
        "crisp.chat",
        "tawk.to",
    ]
    has_live_chat = any(s in low_html for s in live_chat_scripts)

    has_ga = bool(
        re.search(r"\bgtag\(|googletagmanager\.com|ua-\d{4,}|g-[a-z0-9]{6,}", low_html)
    )
    has_fb_pixel = "fbq(" in low_html

    has_blog = "/blog" in low_html or "blog" in raw_text[:2000]

    builder = detect_builder(html)
    site_intel = infer_site_intel(
        low_html=low_html,
        external_script_count=external_script_count,
        html_char_count=html_char_count,
        internal_link_count=internal_link_count,
        builder=builder,
    )

    return {
        "builder": builder,
        "has_online_ordering": has_ordering,
        "has_booking": has_booking,
        "has_ecommerce": ecommerce,
        "has_live_chat": has_live_chat,
        "has_analytics": has_ga,
        "has_facebook_pixel": has_fb_pixel,
        "has_blog": has_blog,
        "duplicate_text_bug": duplicate_text_bug,
        "text_sample": raw_text[:4000],
        "html_char_count": html_char_count,
        "external_script_count": external_script_count,
        "has_viewport_meta": has_viewport_meta,
        "internal_link_count": internal_link_count,
        "site_intel": site_intel,
    }


def copyright_years(html: str) -> list[int]:
    years = [int(y) for y in re.findall(r"(?:©|copyright)\s*(?:199\d|20\d{2})", html, re.I)]
    years += [int(y) for y in re.findall(r"\b(20\d{2})\b", html[:5000])]
    return sorted(set(y for y in years if 1990 <= y <= 2030))
