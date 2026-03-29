"""HTML parsing — builders, features, duplicate text."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, NavigableString

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


def extract_text_and_features(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    raw_text = soup.get_text(" ", strip=True).lower()
    low_html = html.lower()

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

    return {
        "builder": detect_builder(html),
        "has_online_ordering": has_ordering,
        "has_booking": has_booking,
        "has_ecommerce": ecommerce,
        "has_live_chat": has_live_chat,
        "has_analytics": has_ga,
        "has_facebook_pixel": has_fb_pixel,
        "has_blog": has_blog,
        "duplicate_text_bug": duplicate_text_bug,
        "text_sample": raw_text[:4000],
    }


def copyright_years(html: str) -> list[int]:
    years = [int(y) for y in re.findall(r"(?:©|copyright)\s*(?:199\d|20\d{2})", html, re.I)]
    years += [int(y) for y in re.findall(r"\b(20\d{2})\b", html[:5000])]
    return sorted(set(y for y in years if 1990 <= y <= 2030))
