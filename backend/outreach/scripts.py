"""Personalized call scripts."""

from __future__ import annotations

from typing import Any


def generate_call_script(lead: dict[str, Any]) -> str:
    name = lead.get("business_name") or "your business"
    city = lead.get("city") or lead.get("address") or "the area"
    category = lead.get("category") or "local"
    if lead.get("ai_biggest_problem"):
        biggest = lead["ai_biggest_problem"]
    elif lead.get("critical_issues"):
        biggest = lead["critical_issues"][0]
    else:
        biggest = "a few gaps on your website"
    revenue = lead.get("revenue_opportunity_monthly") or 0
    competitors = lead.get("competitors") or []
    competitor_line = ""
    if competitors:
        top = competitors[0]
        cname = top.get("name", "a nearby competitor")
        competitor_line = (
            f"I noticed {cname} is showing up strong online — "
            f"I wanted to reach out before that gap gets bigger."
        )
    else:
        competitor_line = (
            f"I was looking at local {category} businesses around {city} and came across your site."
        )

    revenue_line = ""
    if revenue and revenue > 1000:
        revenue_line = (
            f"Based on your reviews and typical traffic patterns, you could be leaving "
            f"roughly ${revenue:,} per month on the table without the right online setup."
        )

    timeline = "2–4 weeks"
    est = lead.get("ai_estimated_value") or "$2,500–$5,000"

    script = f"""
Hi, is this {name}?

My name is [Your name], I'm a web developer based here in {city}.

{competitor_line}

I noticed {biggest}. {revenue_line}

I specialize in helping {category} businesses in the area — I recently helped a similar business tighten up their site and booking flow.

I can usually have something live within {timeline}, and the investment is typically around {est}.

Would you have 15 minutes this week to walk through what that could look like for {name}? I can show exactly what I'd fix and ballpark numbers.
""".strip()
    return script
