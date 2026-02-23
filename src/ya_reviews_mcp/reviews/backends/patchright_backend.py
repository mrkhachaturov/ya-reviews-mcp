"""Patchright browser backend (anti-detection Playwright fork)."""
from __future__ import annotations

import logging
from typing import Any

from ya_reviews_mcp.exceptions import BrowserError
from ya_reviews_mcp.reviews.backends.base import BaseBrowserBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig

logger = logging.getLogger("ya-reviews")


def _import_patchright() -> Any:
    """Lazy import patchright to allow it to be an optional dependency."""
    try:
        from patchright.async_api import async_playwright
        return async_playwright
    except ImportError as exc:
        raise BrowserError(
            "Patchright is not installed. "
            "Install it with: pip install ya-reviews-mcp[patchright]"
        ) from exc


class PatchrightBackend(BaseBrowserBackend):
    """Browser backend using Patchright (anti-detection Playwright fork)."""

    @property
    def handles_stealth(self) -> bool:
        """Patchright patches navigator.webdriver natively."""
        return True

    def __init__(self, config: YaReviewsConfig) -> None:
        self._config = config
        self._playwright: Any = None
        self._browser: Any = None

    async def start(self) -> None:
        async_playwright = _import_patchright()
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
                "Patchright browser launched (headless=%s)",
                self._config.headless,
            )
        except BrowserError:
            raise
        except Exception as exc:
            raise BrowserError(
                f"Failed to launch Patchright browser: {exc}"
            ) from exc

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Patchright browser closed")

    async def new_context(self, **kwargs: Any) -> Any:
        if self._browser is None:
            raise BrowserError("Browser not started. Call start() first.")
        return await self._browser.new_context(**kwargs)
