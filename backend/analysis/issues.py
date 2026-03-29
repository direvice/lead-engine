"""Deterministic issue detection from extracted features + PageSpeed."""

from __future__ import annotations

from typing import Any


def build_issues(
    features: dict[str, Any],
    pagespeed: dict[str, Any],
    scraped: dict[str, Any],
    category: str | None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    issues: list[dict[str, Any]] = []
    critical: list[str] = []
    missing: list[str] = []

    cat = (category or "").lower()

    if scraped.get("load_error"):
        issues.append(
            {
                "severity": "critical",
                "code": "load_failure",
                "title": "Site failed to load",
                "description": scraped["load_error"][:300],
                "impact": 25,
            }
        )
        critical.append("Site does not load reliably in a browser")

    if scraped.get("robots_blocked"):
        issues.append(
            {
                "severity": "high",
                "code": "robots",
                "title": "Robots.txt blocked automated review",
                "description": "We could not fetch the site per robots rules.",
                "impact": 10,
            }
        )

    if features.get("duplicate_text_bug"):
        issues.append(
            {
                "severity": "high",
                "code": "duplicate_text",
                "title": "Duplicate text blocks detected",
                "description": "Repeated long text chunks often indicate template bugs.",
                "impact": 12,
            }
        )
        critical.append("Duplicate content / rendering bug")

    perf = pagespeed.get("performance_score")
    if perf is not None and perf < 50:
        issues.append(
            {
                "severity": "high",
                "code": "low_pagespeed",
                "title": "Poor mobile PageSpeed score",
                "description": f"Lighthouse performance ~{perf}/100.",
                "impact": 18,
            }
        )
        critical.append("Very slow mobile experience")

    if scraped.get("has_horizontal_scroll"):
        issues.append(
            {
                "severity": "medium",
                "code": "mobile_overflow",
                "title": "Mobile horizontal scroll",
                "description": "Layout wider than mobile viewport.",
                "impact": 10,
            }
        )

    if not features.get("has_analytics"):
        issues.append(
            {
                "severity": "low",
                "code": "no_analytics",
                "title": "No obvious analytics",
                "description": "No GA/GTM snippet detected.",
                "impact": 8,
            }
        )

    if not features.get("has_blog"):
        issues.append(
            {
                "severity": "low",
                "code": "no_blog",
                "title": "No blog / content hub",
                "description": "Limited ongoing SEO content signals.",
                "impact": 6,
            }
        )

    if "restaurant" in cat or "food" in cat or "cafe" in cat:
        if not features.get("has_online_ordering"):
            missing.append("online_ordering")
            issues.append(
                {
                    "severity": "high",
                    "code": "no_ordering",
                    "title": "No online ordering detected",
                    "description": "Competitors often capture delivery/pickup orders online.",
                    "impact": 15,
                }
            )

    if any(
        x in cat
        for x in (
            "salon",
            "spa",
            "dentist",
            "doctor",
            "health",
            "lawyer",
            "account",
            "beauty",
        )
    ):
        if not features.get("has_booking"):
            missing.append("booking")
            issues.append(
                {
                    "severity": "high",
                    "code": "no_booking",
                    "title": "No online booking",
                    "description": "Appointment-based businesses lose calls to competitors with booking.",
                    "impact": 15,
                }
            )

    if "store" in cat or "retail" in cat or "shop" in cat:
        if not features.get("has_ecommerce"):
            missing.append("ecommerce")
            issues.append(
                {
                    "severity": "medium",
                    "code": "no_ecom",
                    "title": "No e-commerce detected",
                    "description": "Consider capturing online sales or BOPIS.",
                    "impact": 12,
                }
            )

    if scraped.get("page_errors"):
        issues.append(
            {
                "severity": "critical",
                "code": "js_errors",
                "title": "JavaScript errors on page",
                "description": "; ".join(scraped["page_errors"][:3]),
                "impact": 20,
            }
        )
        critical.append("Active errors in browser console")

    return issues, critical, missing
