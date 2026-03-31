"""Playwright-based deep scrape."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from playwright.async_api import async_playwright

from scraping.screenshot import compress_screenshot, save_screenshot

logger = logging.getLogger(__name__)

UA = "FoxValleyDigital-LeadBot/1.0"


@dataclass
class ScrapedData:
    html: Optional[str] = None
    load_time_ms: int = 0
    has_horizontal_scroll: bool = False
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    network_sample: list[dict[str, Any]] = field(default_factory=list)
    robots_blocked: bool = False
    load_error: Optional[str] = None
    desktop_path: Optional[str] = None
    mobile_path: Optional[str] = None


async def check_robots_allowed(url: str) -> bool:
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{base}/robots.txt"
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            r = await client.get(robots_url)
            if r.status_code != 200:
                return True
            path = parsed.path or "/"
            lines = r.text.splitlines()
            applies = False
            for line in lines:
                low = line.strip().lower()
                if low.startswith("user-agent:"):
                    ua = low.split(":", 1)[1].strip()
                    applies = ua == "*" or UA.lower() in ua.lower()
                elif applies and low.startswith("disallow:"):
                    dis = low.split(":", 1)[1].strip()
                    if not dis:
                        continue
                    if path.startswith(dis) or dis == "/":
                        return False
            return True
    except Exception as e:
        logger.debug("robots check: %s", e)
        return True


class WebScraper:
    async def scrape(self, url: str, lead_id: int) -> ScrapedData:
        if not url or not url.startswith("http"):
            return ScrapedData(load_error="invalid_url")

        allowed = await check_robots_allowed(url)
        if not allowed:
            return ScrapedData(robots_blocked=True)

        console_errors: list[str] = []
        page_errors: list[str] = []
        responses: list[dict[str, Any]] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            try:
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent=UA,
                    ignore_https_errors=True,
                )
                page = await context.new_page()

                def on_console(msg) -> None:
                    if msg.type == "error":
                        console_errors.append(msg.text[:500])

                def on_page_error(err) -> None:
                    page_errors.append(str(err)[:500])

                def on_response(resp) -> None:
                    try:
                        responses.append(
                            {
                                "url": resp.url[:300],
                                "status": resp.status,
                            }
                        )
                    except Exception:
                        pass

                page.on("console", on_console)
                page.on("pageerror", on_page_error)
                page.on("response", on_response)

                start = time.time()
                try:
                    await page.goto(url, wait_until="networkidle", timeout=15000)
                except Exception as e:
                    return ScrapedData(load_error=str(e))

                load_time = int((time.time() - start) * 1000)
                desktop_shot = await page.screenshot(full_page=False)
                desktop_compressed = compress_screenshot(desktop_shot, max_kb=150)
                html = await page.content()

                await page.set_viewport_size({"width": 375, "height": 812})
                await page.wait_for_timeout(500)
                mobile_shot = await page.screenshot(full_page=False)
                mobile_width = await page.evaluate("document.body.scrollWidth")
                has_horizontal_scroll = bool(mobile_width and mobile_width > 380)
                mobile_compressed = compress_screenshot(mobile_shot, max_kb=100)

                dpath = save_screenshot(
                    desktop_compressed, f"{lead_id}_desktop_{int(time.time())}.jpg"
                )
                mpath = save_screenshot(
                    mobile_compressed, f"{lead_id}_mobile_{int(time.time())}.jpg"
                )

                return ScrapedData(
                    html=html,
                    load_time_ms=load_time,
                    has_horizontal_scroll=has_horizontal_scroll,
                    console_errors=console_errors[:50],
                    page_errors=page_errors[:50],
                    network_sample=responses[:200],
                    desktop_path=dpath,
                    mobile_path=mpath,
                )
            except Exception as e:
                logger.exception("Playwright scrape failed for %s: %s", url, e)
                return ScrapedData(load_error=str(e))
            finally:
                try:
                    await browser.close()
                except Exception:
                    pass
