"""Ollama HTTP client — local free inference."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2",
        json_mode: bool = True,
        timeout: float = 120.0,
    ) -> str:
        last_err: Optional[Exception] = None
        models_to_try = [model, "mistral", "llama3.2"]
        seen: set[str] = set()
        for m in models_to_try:
            if m in seen:
                continue
            seen.add(m)
            for attempt in range(3):
                try:
                    body: dict[str, Any] = {
                        "model": m,
                        "prompt": prompt,
                        "stream": False,
                    }
                    if json_mode:
                        body["format"] = "json"
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        r = await client.post(
                            f"{self.base_url}/api/generate",
                            json=body,
                        )
                        r.raise_for_status()
                        data = r.json()
                        return (data.get("response") or "").strip()
                except Exception as e:
                    last_err = e
                    logger.warning("Ollama generate attempt %s model %s: %s", attempt + 1, m, e)
        if last_err:
            raise last_err
        return ""

    async def classify(self, text: str, options: list[str]) -> str:
        from ai.prompts import CLASSIFY_PROMPT

        opts = ", ".join(f'"{o}"' for o in options)
        prompt = CLASSIFY_PROMPT.format(options=opts, text=text[:8000])
        raw = await self.generate(prompt, model="phi3:mini", json_mode=False, timeout=60.0)
        raw_clean = raw.strip().strip('"').strip()
        for o in options:
            if o.lower() in raw_clean.lower() or raw_clean.lower() in o.lower():
                return o
        return options[0] if options else raw_clean
