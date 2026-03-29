"""Screenshot compression and persistence."""

from __future__ import annotations

import io
import os

from PIL import Image

from config import get_settings


def compress_screenshot(raw: bytes, max_kb: int = 150, quality_start: int = 82) -> bytes:
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    q = quality_start
    while q >= 45:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True)
        data = buf.getvalue()
        if len(data) <= max_kb * 1024:
            return data
        q -= 8
    return buf.getvalue()


def save_screenshot(data: bytes, filename: str) -> str:
    settings = get_settings()
    os.makedirs(settings.screenshot_dir, exist_ok=True)
    path = os.path.join(settings.screenshot_dir, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path
