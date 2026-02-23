"""Yandex Reviews configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class YaReviewsConfig:
    headless: bool = True
    page_timeout: int = 30000
    intercept_timeout: int = 15000
    request_delay: float = 2.0
    max_pages: int = 20
    retries: int = 3
    retry_delay: float = 2.0
    browser_locale: str = "ru-RU"
    enabled_tools: list[str] | None = None
    browser_ws_url: str | None = None
    backend: str = "playwright"

    @classmethod
    def from_env(cls) -> YaReviewsConfig:
        enabled_raw = os.environ.get("ENABLED_TOOLS", "").strip()
        enabled_tools: list[str] | None = (
            [t.strip() for t in enabled_raw.split(",") if t.strip()]
            if enabled_raw
            else None
        )
        return cls(
            headless=os.environ.get("BROWSER_HEADLESS", "true").lower() != "false",
            page_timeout=int(os.environ.get("PAGE_TIMEOUT", "30000")),
            intercept_timeout=int(os.environ.get("INTERCEPT_TIMEOUT", "15000")),
            request_delay=float(os.environ.get("REQUEST_DELAY", "2.0")),
            max_pages=int(os.environ.get("MAX_PAGES", "20")),
            retries=int(os.environ.get("SCRAPER_RETRIES", "3")),
            retry_delay=float(os.environ.get("SCRAPER_RETRY_DELAY", "2.0")),
            browser_locale=os.environ.get("BROWSER_LOCALE", "ru-RU"),
            enabled_tools=enabled_tools,
            browser_ws_url=os.environ.get("BROWSER_WS_URL"),
            backend=os.environ.get("BROWSER_BACKEND", "playwright"),
        )
