"""Self-learning layer: user teaching + outcomes adjust lead scores from accumulated patterns."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from models import BusinessLead, LearningSignal, SettingsRow

logger = logging.getLogger(__name__)

SETTINGS_KEY = "learned_patterns"
MAX_MULT = 1.12
MIN_MULT = 0.88


def _pattern_key(smb_fit: dict[str, Any] | None, builder: str | None) -> str:
    tier = (smb_fit or {}).get("target_tier") or "unknown"
    b = builder or "unknown"
    return f"{tier}|{b}"


def _get_or_create_profile(db: Session) -> SettingsRow:
    row = db.get(SettingsRow, SETTINGS_KEY)
    if row is None:
        row = SettingsRow(key=SETTINGS_KEY, value={"buckets": {}, "total_signals": 0})
        db.add(row)
        db.flush()
        db.refresh(row)
    return row


def record_teaching_signal(db: Session, lead: BusinessLead, signal: str) -> dict[str, Any]:
    """
    signal: good_target | bad_target | outcome_won | outcome_skip
    """
    smb = {}
    if isinstance(lead.features, dict):
        smb = lead.features.get("smb_fit") or {}
    ctx = {
        "tier": smb.get("target_tier"),
        "builder": lead.website_builder,
        "category": lead.category,
    }
    db.add(LearningSignal(lead_id=lead.id, signal=signal, context=ctx))

    row = _get_or_create_profile(db)
    val = dict(row.value or {})
    buckets = val.setdefault("buckets", {})
    key = _pattern_key(smb, lead.website_builder)
    b = buckets.setdefault(key, {"good": 0, "bad": 0})

    if signal in ("good_target", "outcome_won"):
        b["good"] += 1
    elif signal in ("bad_target", "outcome_skip"):
        b["bad"] += 1

    val["total_signals"] = int(val.get("total_signals") or 0) + 1
    row.value = val
    db.flush()
    logger.info("Learning signal %s lead=%s pattern=%s", signal, lead.id, key)
    return {"pattern": key, "bucket": b}


def pattern_multiplier(db: Session, smb_fit: dict[str, Any] | None, builder: str | None) -> float:
    row = db.get(SettingsRow, SETTINGS_KEY)
    if not row or not row.value:
        return 1.0
    buckets = (row.value or {}).get("buckets") or {}
    key = _pattern_key(smb_fit, builder)
    b = buckets.get(key) or {"good": 0, "bad": 0}
    g, bad = int(b.get("good") or 0), int(b.get("bad") or 0)
    n = g + bad
    if n == 0:
        return 1.0
    # Net trust in this pattern: positive = you keep marking these winners
    confidence = (g - bad) / n
    mult = 1.0 + 0.10 * confidence
    return max(MIN_MULT, min(MAX_MULT, mult))


def apply_pattern_multiplier(
    db: Session, lead_score: float, smb_fit: dict[str, Any] | None, builder: str | None
) -> float:
    m = pattern_multiplier(db, smb_fit, builder)
    return min(100.0, max(0.0, round(lead_score * m, 1)))


def intelligence_brief(db: Session) -> dict[str, Any]:
    row = db.get(SettingsRow, SETTINGS_KEY)
    val = (row.value if row else None) or {}
    buckets = val.get("buckets") or {}
    total = int(val.get("total_signals") or 0)

    ranked: list[dict[str, Any]] = []
    for pattern, b in buckets.items():
        g, bad = int(b.get("good") or 0), int(b.get("bad") or 0)
        n = g + bad
        if n == 0:
            continue
        net = (g - bad) / n
        ranked.append(
            {
                "pattern": pattern,
                "good": g,
                "bad": bad,
                "n": n,
                "net_confidence": round(net, 3),
            }
        )
    ranked.sort(key=lambda x: (-x["n"], -x["net_confidence"]))

    sig_n = db.query(LearningSignal).count()

    hint = _generate_hint(ranked[:5], total)
    return {
        "learned_signals_stored": sig_n,
        "pattern_updates": total,
        "top_patterns": ranked[:8],
        "coaching_hint": hint,
    }


def _generate_hint(top: list[dict[str, Any]], total: int) -> str:
    if total == 0:
        return (
            "Teach the model from lead dossiers (👍 / 👎) or mark Won/Skip — "
            "scores gently adapt to what you actually convert."
        )
    best = top[0] if top else None
    if best and best["net_confidence"] >= 0.4 and best["n"] >= 2:
        tier, _, builder = best["pattern"].partition("|")
        return (
            f"Strong positive pattern: {tier} + {builder} "
            f"({best['good']} wins vs {best['bad']} negatives). "
            f"Prioritize similar rows in your queue."
        )
    if best and best["net_confidence"] <= -0.25:
        return (
            f"You often pass on `{best['pattern']}`. Consider tightening discovery or "
            "using 👎 on bad targets so scores drift down for that profile."
        )
    return (
        f"{total} teaching updates recorded. Keep labeling — "
        "the engine boosts scores for profiles you confirm and dampens ones you reject."
    )


def recalculate_all_scores(db: Session) -> dict[str, Any]:
    """
    Re-apply learning multipliers using stored _score_pre_learning from last full analysis.
    Leads analyzed before that field existed are skipped.
    """
    updated = 0
    skipped = 0
    for lead in db.query(BusinessLead).all():
        feats = lead.features if isinstance(lead.features, dict) else {}
        pre = feats.get("_score_pre_learning")
        if pre is None:
            skipped += 1
            continue
        smb = feats.get("smb_fit") or {}
        new_s = apply_pattern_multiplier(db, float(pre), smb, lead.website_builder)
        lead.lead_score = new_s
        updated += 1
    db.commit()
    return {
        "scores_recalculated": updated,
        "skipped_no_baseline": skipped,
        "hint": "Re-run a scan or rescore job on old leads to populate score baselines.",
    }
