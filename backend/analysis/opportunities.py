"""High-level opportunity flags."""

from __future__ import annotations

from typing import Any


def summarize_opportunities(
    features: dict[str, Any], no_website: bool, builder: str | None
) -> list[str]:
    opps: list[str] = []
    if no_website:
        opps.append("no_website")
    if builder:
        opps.append(f"builder_site:{builder}")
    if not features.get("has_online_ordering"):
        opps.append("ordering_gap_possible")
    if not features.get("has_ecommerce"):
        opps.append("ecom_gap_possible")
    if not features.get("has_booking"):
        opps.append("booking_gap_possible")
    if not features.get("has_live_chat"):
        opps.append("no_live_chat")
    return opps
