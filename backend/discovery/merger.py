"""Deduplicate and merge businesses from multiple sources."""

from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz


def _norm_phone(p: str | None) -> str | None:
    if not p:
        return None
    digits = re.sub(r"\D", "", p)
    if len(digits) >= 10:
        return digits[-10:]
    return digits or None


def _norm_name(n: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (n or "").lower()).strip()


def _city_key(addr: str | None) -> str:
    if not addr:
        return ""
    parts = [p.strip().lower() for p in addr.split(",")]
    return parts[-2] if len(parts) >= 2 else parts[0] if parts else ""


def _merge_record(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if v is None or v == "":
            continue
        if k == "source_ids":
            merged = dict(out.get("source_ids") or {})
            merged.update(v or {})
            out["source_ids"] = merged
        elif k == "types":
            ta = list(out.get("types") or [])
            tb = list(v or [])
            out["types"] = list(dict.fromkeys(ta + tb))
        elif out.get(k) in (None, "", []):
            out[k] = v
        elif k in ("google_rating", "review_count") and v:
            if (out.get(k) or 0) < (v or 0):
                out[k] = v
    out["source"] = "merged"
    return out


def merge_business_lists(groups: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for g in groups:
        flat.extend(g)

    clusters: list[list[dict[str, Any]]] = []
    used = [False] * len(flat)

    for i, a in enumerate(flat):
        if used[i]:
            continue
        cluster = [a]
        used[i] = True
        phone_a = _norm_phone(a.get("phone"))
        name_a = _norm_name(a.get("business_name"))
        city_a = _city_key(a.get("address"))
        addr_a = (a.get("address") or "").lower()

        for j, b in enumerate(flat):
            if used[j]:
                continue
            phone_b = _norm_phone(b.get("phone"))
            name_b = _norm_name(b.get("business_name"))
            city_b = _city_key(b.get("address"))
            addr_b = (b.get("address") or "").lower()

            same_phone = phone_a and phone_b and phone_a == phone_b
            name_sim = fuzz.token_sort_ratio(name_a, name_b)
            same_city = city_a and city_b and city_a == city_b
            name_match = name_sim >= 85 and same_city
            addr_sim = fuzz.ratio(addr_a, addr_b) if addr_a and addr_b else 0
            addr_match = addr_sim >= 90 and bool(addr_a)

            if same_phone or name_match or addr_match:
                cluster.append(b)
                used[j] = True
        clusters.append(cluster)

    merged: list[dict[str, Any]] = []
    for c in clusters:
        base = c[0]
        for other in c[1:]:
            base = _merge_record(base, other)
        merged.append(base)
    return merged
