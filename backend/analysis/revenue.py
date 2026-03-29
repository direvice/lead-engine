"""Conservative monthly revenue opportunity estimates."""

from __future__ import annotations

from typing import Any


def _category_bucket(category: str | None) -> str:
    c = (category or "").lower()
    if any(x in c for x in ("restaurant", "food", "cafe", "bar", "bakery", "meal")):
        return "restaurant"
    if any(x in c for x in ("store", "retail", "shop", "clothing", "gift")):
        return "retail"
    return "service"


def estimate_category_searches(category: str | None, city: str | None) -> int:
    # Rough benchmark placeholder — conservative
    base = 800
    if category:
        base += min(len(category) * 10, 400)
    return base


def compute_revenue_opportunity(
    category: str | None,
    review_count: int | None,
    rating: float | None,
    features: dict[str, Any],
    no_website: bool,
    city: str | None,
) -> tuple[int, str]:
    rc = review_count or 0
    bucket = _category_bucket(category)

    if no_website:
        searches = estimate_category_searches(category, city)
        avg_service = 75
        monthly = int(searches * 0.05 * avg_service * 0.25)
        monthly = max(400, min(monthly, 25000))
        desc = (
            f"You're invisible to roughly {searches} monthly local searches for "
            f"{category or 'your category'} — a site could capture a slice of that demand."
        )
        return monthly, desc

    if bucket == "restaurant":
        if features.get("has_online_ordering"):
            return 0, "Online ordering already present — focus on conversion/performance."
        avg_monthly_customers = max(rc * 2, 400)
        avg_check = 25
        online_order_rate = 0.12
        avg_online_check = avg_check * 1.15
        monthly = int(avg_monthly_customers * online_order_rate * avg_online_check)
        monthly = max(300, min(monthly, 40000))
        desc = f"Adding online ordering could bring in ~${monthly:,}/mo (conservative estimate)."
        return monthly, desc

    if bucket == "retail":
        if features.get("has_ecommerce"):
            return 0, "E-commerce signals present."
        avg_ticket = 45
        online_multiplier = 0.15
        estimated_monthly = max(rc * 12, 300) * avg_ticket // 100
        monthly = int(max(300, estimated_monthly * online_multiplier))
        monthly = min(monthly, 35000)
        desc = f"E-commerce could add ~${monthly:,}/mo in incremental online sales (estimate)."
        return monthly, desc

    # service
    if features.get("has_booking"):
        return 0, "Booking tooling detected."
    appointments_per_day = 8
    missed_booking_rate = 0.12
    avg_service_value = 95
    if any(x in (category or "").lower() for x in ("dentist", "doctor", "lawyer")):
        avg_service_value = 180
    monthly = int(appointments_per_day * missed_booking_rate * avg_service_value * 22)
    monthly = max(350, min(monthly, 45000))
    desc = f"Online booking could recover ~${monthly:,}/mo in missed appointments (estimate)."
    return monthly, desc
