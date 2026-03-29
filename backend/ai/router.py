"""Route AI tasks: Ollama first to preserve Gemini quota (project rule)."""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Any, Literal, Optional

from ai.gemini_client import GeminiClient
from ai.ollama_client import OllamaClient
from ai.prompts import JSON_RETRY_SUFFIX

logger = logging.getLogger(__name__)

TaskType = Literal["full_analysis", "classify", "pitch"]


def _strip_json_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _parse_json(text: str) -> Optional[dict[str, Any]]:
    try:
        return json.loads(_strip_json_fence(text))
    except json.JSONDecodeError:
        return None


class AIRouter:
    def __init__(self, ollama: OllamaClient, gemini: Optional[GeminiClient]):
        self.ollama = ollama
        self.gemini: Optional[GeminiClient] = gemini
        self.gemini_count = 0
        self.gemini_daily_limit = 1400
        self._gemini_day: Optional[date] = None

    def _reset_daily_if_needed(self) -> None:
        today = date.today()
        if self._gemini_day != today:
            self._gemini_day = today
            self.gemini_count = 0

    def _can_use_gemini(self) -> bool:
        self._reset_daily_if_needed()
        return (
            self.gemini is not None
            and self.gemini.configured()
            and self.gemini_count < self.gemini_daily_limit
        )

    async def _ollama_json(self, prompt: str) -> dict[str, Any]:
        raw = await self.ollama.generate(prompt, model="llama3.2", json_mode=True)
        parsed = _parse_json(raw)
        if parsed is not None:
            return parsed
        raw2 = await self.ollama.generate(
            prompt + JSON_RETRY_SUFFIX, model="llama3.2", json_mode=True
        )
        parsed2 = _parse_json(raw2)
        if parsed2 is not None:
            return parsed2
        raise ValueError("Invalid JSON from Ollama")

    async def _gemini_json(self, prompt: str) -> dict[str, Any]:
        if not self._can_use_gemini():
            raise RuntimeError("Gemini unavailable or over quota")
        raw = await self.gemini.generate(prompt, json_mode=True)
        self.gemini_count += 1
        parsed = _parse_json(raw)
        if parsed is not None:
            return parsed
        raw2 = await self.gemini.generate(prompt + JSON_RETRY_SUFFIX, json_mode=True)
        self.gemini_count += 1
        parsed2 = _parse_json(raw2)
        if parsed2 is not None:
            return parsed2
        raise ValueError("Invalid JSON from Gemini")

    async def analyze(
        self, prompt: str, task_type: TaskType
    ) -> tuple[dict[str, Any], str]:
        """
        Returns (parsed_json, model_label).
        classify → phi3:mini via Ollama (non-JSON return handled in classify path).
        pitch → Ollama first, then Gemini if JSON invalid.
        full_analysis → Ollama first (save quota), then Gemini fallback.
        """
        if task_type == "classify":
            # classify uses separate API on OllamaClient
            raise ValueError("Use ollama.classify for classify tasks")

        if task_type == "pitch":
            try:
                data = await self._ollama_json(prompt)
                return data, "ollama-llama3.2"
            except Exception as e:
                logger.warning("Ollama pitch failed, trying Gemini: %s", e)
                if self._can_use_gemini():
                    try:
                        data = await self._gemini_json(prompt)
                        return data, "gemini-flash"
                    except Exception as e2:
                        logger.warning("Gemini pitch failed: %s", e2)
                raise

        # full_analysis
        try:
            data = await self._ollama_json(prompt)
            return data, "ollama-llama3.2"
        except Exception as e:
            logger.warning("Ollama full_analysis failed, trying Gemini: %s", e)
            if self._can_use_gemini():
                try:
                    data = await self._gemini_json(prompt)
                    return data, "gemini-flash"
                except Exception as e2:
                    logger.warning("Gemini full_analysis failed: %s", e2)
            raise
