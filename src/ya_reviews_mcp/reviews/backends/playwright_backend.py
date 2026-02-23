"""Playwright browser backend."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from playwright.async_api import async_playwright

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Playwright

from ya_reviews_mcp.exceptions import BrowserError
from ya_reviews_mcp.reviews.backends.base import BaseBrowserBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig

logger = logging.getLogger("ya-reviews")


class PlaywrightBackend(BaseBrowserBackend):
    """Browser backend using Playwright."""

    def __init__(self, config: YaReviewsConfig) -> None:
        self._config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._config.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            logger.info(
                "Playwright browser launched (headless=%s)",
                self._config.headless,
            )
        except Exception as exc:
            raise BrowserError(
                f"Failed to launch Playwright browser: {exc}"
            ) from exc

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Playwright browser closed")

    async def new_context(self, **kwargs: Any) -> BrowserContext:
        if self._browser is None:
            raise BrowserError("Browser not started. Call start() first.")
        return await self._browser.new_context(**kwargs)
