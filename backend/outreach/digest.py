"""Morning digest HTML."""

from __future__ import annotations

from typing import Any


def build_morning_digest_html(
    *,
    new_leads: list[dict[str, Any]],
    scanned_count: int,
    category: str,
    dashboard_url: str,
    next_scan_hint: str,
) -> str:
    top = sorted(
        new_leads,
        key=lambda x: (x.get("revenue_opportunity_monthly") or 0, x.get("lead_score") or 0),
        reverse=True,
    )[:3]
    rows = []
    for L in top:
        rows.append(
            f"<li><strong>{L.get('business_name')}</strong> — {L.get('category')} in {L.get('city') or ''}<br>"
            f"Score: {L.get('lead_score')}/100 | Opportunity: ${L.get('revenue_opportunity_monthly') or 0:,}/mo<br>"
            f"Issue: {L.get('ai_biggest_problem') or '—'}<br>"
            f"Pitch: {L.get('ai_pitch') or '—'}<br>"
            f"Call: {L.get('phone') or '—'}<br>"
            f'<a href="{dashboard_url}/leads/{L.get("id")}">View full details →</a></li>'
        )
    return f"""
<html><body style="font-family:system-ui,sans-serif">
<p>Good morning! Here's what the bot found last night.</p>
<h3>Top leads</h3>
<ul>{"".join(rows)}</ul>
<h3>Stats</h3>
<ul>
<li>Total scanned last night: {scanned_count}</li>
<li>New leads added: {len(new_leads)}</li>
<li>Category scanned: {category}</li>
<li>Next scan: {next_scan_hint}</li>
</ul>
</body></html>
"""
