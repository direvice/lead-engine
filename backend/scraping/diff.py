"""Screenshot change detection."""

from __future__ import annotations

import os
from typing import Any

import numpy as np
from PIL import Image, ImageChops


def describe_change(pct: float) -> str:
    if pct > 15:
        return "Major visual change vs last capture — site may have been redesigned."
    if pct > 3:
        return "Minor changes detected since last scan."
    return "No meaningful visual change."


def detect_changes(old_screenshot_path: str, new_screenshot_path: str) -> dict[str, Any]:
    if not os.path.isfile(old_screenshot_path) or not os.path.isfile(new_screenshot_path):
        return {
            "status": "unknown",
            "change_percentage": 0.0,
            "description": "Missing prior or new screenshot.",
        }
    old = Image.open(old_screenshot_path).convert("RGB")
    new = Image.open(new_screenshot_path).convert("RGB")
    new = new.resize(old.size)
    diff = ImageChops.difference(old, new)
    arr = np.array(diff)
    change_pct = float((arr > 20).sum() / arr.size * 100)

    if change_pct > 15:
        status = "major_change"
    elif change_pct > 3:
        status = "minor_change"
    else:
        status = "no_change"

    return {
        "status": status,
        "change_percentage": round(change_pct, 1),
        "description": describe_change(change_pct),
    }
