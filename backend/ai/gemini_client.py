"""Google Gemini client — free tier with rate limiting."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore


class GeminiClient:
    """Async-friendly wrapper; runs sync SDK in executor."""

    def __init__(self, api_key: str):
        self.api_key = api_key or ""
        self._model = None
        if genai and self.api_key:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel("gemini-1.5-flash")
        self._minute_requests: deque[float] = deque(maxlen=20)
        self._lock = asyncio.Lock()

    def configured(self) -> bool:
        return self._model is not None

    async def _rate_limit(self) -> None:
        async with self._lock:
            now = time.time()
            while self._minute_requests and now - self._minute_requests[0] > 60:
                self._minute_requests.popleft()
            if len(self._minute_requests) >= 14:
                wait = 60 - (now - self._minute_requests[0]) + 0.5
                if wait > 0:
                    await asyncio.sleep(wait)
            self._minute_requests.append(time.time())

    async def generate(self, prompt: str, json_mode: bool = True) -> str:
        if not self._model:
            raise RuntimeError("Gemini not configured")
        await self._rate_limit()

        def _call() -> str:
            kwargs: dict[str, Any] = {}
            if json_mode:
                kwargs["generation_config"] = genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            resp = self._model.generate_content(prompt, **kwargs)
            return (resp.text or "").strip()

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, _call)
        except Exception as e:
            logger.warning("Gemini generate failed: %s", e)
            raise
