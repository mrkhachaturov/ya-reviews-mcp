"""Remote CDP browser backend (connects to external browser via WebSocket)."""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Playwright

from ya_reviews_mcp.exceptions import BrowserError
from ya_reviews_mcp.reviews.backends.base import BaseBrowserBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig

logger = logging.getLogger("ya-reviews")


def _resolve_ws_url(url: str) -> str:
    """Resolve a CDP endpoint to a full WebSocket debugger URL.

    Accepts:
      - ws://host:port/devtools/browser/... (returned as-is)
      - ws://host:port or http://host:port (auto-discovers via /json/version)
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Already a full debugger URL
    if "/devtools/" in path:
        return url

    # Auto-discover from /json/version endpoint
    http_url = f"http://{parsed.hostname}:{parsed.port}/json/version"
    try:
        with urllib.request.urlopen(http_url, timeout=5) as resp:
            data = json.loads(resp.read())
        ws_debugger_url: str = data["webSocketDebuggerUrl"]
        logger.info("Discovered WS URL: %s", ws_debugger_url)
        return ws_debugger_url
    except Exception as exc:
        logger.warning(
            "Could not auto-discover WS URL from %s: %s. "
            "Using original URL as-is.",
            http_url, exc,
        )
        return url


class RemoteCDPBackend(BaseBrowserBackend):
    """Browser backend connecting to an external browser via CDP WebSocket.

    Requires a running browser with CDP enabled (e.g., Browserless,
    standalone Chrome with --remote-debugging-port).

    The BROWSER_WS_URL can be:
      - A full WS debugger URL: ws://host:port/devtools/browser/<id>
      - A short URL: ws://host:port (auto-discovers the debugger URL)
    """

    def __init__(self, config: YaReviewsConfig) -> None:
        self._config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        if not self._config.browser_ws_url:
            raise BrowserError(
                "Remote backend requires BROWSER_WS_URL to be set. "
                "Example: ws://localhost:9222"
            )
        ws_url = _resolve_ws_url(self._config.browser_ws_url)
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.connect_over_cdp(
                ws_url,
            )
            logger.info("Connected to remote browser at %s", ws_url)
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
