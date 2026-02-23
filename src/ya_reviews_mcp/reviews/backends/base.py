"""Abstract base class for browser backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseBrowserBackend(ABC):
    """Interface every browser backend must implement.

    Each backend provides a Playwright-compatible Browser object.
    The scraper uses standard Playwright Page/BrowserContext APIs.
    """

    @abstractmethod
    async def start(self) -> None:
        """Launch or connect to a browser."""

    @abstractmethod
    async def close(self) -> None:
        """Shut down the browser or disconnect."""

    @property
    def handles_stealth(self) -> bool:
        """Whether the backend handles anti-detection natively.

        When True, the scraper skips its own navigator.webdriver override
        to avoid conflicts with the backend's stealth patches.
        """
        return False

    @abstractmethod
    async def new_context(self, **kwargs: Any) -> Any:
        """Create a fresh, isolated browser context.

        Returns a Playwright-compatible BrowserContext.
        """
