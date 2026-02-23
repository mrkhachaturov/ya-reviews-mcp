"""Remote CDP browser backend (connects to external browser via WebSocket)."""
from __future__ import annotations

import logging
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Playwright,
    async_playwright,
)

from ya_reviews_mcp.exceptions import BrowserError
from ya_reviews_mcp.reviews.backends.base import BaseBrowserBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig

logger = logging.getLogger("ya-reviews")


class RemoteCDPBackend(BaseBrowserBackend):
    """Browser backend connecting to an external browser via CDP WebSocket.

    Requires a running browser with CDP enabled (e.g., Browserless,
    standalone Chrome with --remote-debugging-port).
    """

    def __init__(self, config: YaReviewsConfig) -> None:
        self._config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        if not self._config.browser_ws_url:
            raise BrowserError(
                "Remote backend requires BROWSER_WS_URL to be set. "
                "Example: ws://localhost:3000"
            )
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.connect_over_cdp(
                self._config.browser_ws_url,
            )
            logger.info(
                "Connected to remote browser at %s",
                self._config.browser_ws_url,
            )
        except BrowserError:
            raise
        except Exception as exc:
            raise BrowserError(
                f"Failed to connect to remote browser at "
                f"{self._config.browser_ws_url}: {exc}"
            ) from exc

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Disconnected from remote browser")

    async def new_context(self, **kwargs: Any) -> BrowserContext:
        if self._browser is None:
            raise BrowserError("Browser not connected. Call start() first.")
        return await self._browser.new_context(**kwargs)
