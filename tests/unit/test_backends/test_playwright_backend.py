"""Tests for PlaywrightBackend."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ya_reviews_mcp.reviews.backends.playwright_backend import PlaywrightBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig


class TestPlaywrightBackendStartClose:
    @pytest.mark.asyncio
    async def test_start_launches_chromium(self) -> None:
        config = YaReviewsConfig()
        backend = PlaywrightBackend(config)

        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch(
            "ya_reviews_mcp.reviews.backends.playwright_backend.async_playwright"
        ) as mock_apw:
            mock_apw.return_value.start = AsyncMock(return_value=mock_pw)
            await backend.start()

        mock_pw.chromium.launch.assert_called_once()
        assert backend._browser is mock_browser

    @pytest.mark.asyncio
    async def test_close_stops_browser_and_playwright(self) -> None:
        config = YaReviewsConfig()
        backend = PlaywrightBackend(config)
        backend._browser = AsyncMock()
        backend._playwright = AsyncMock()

        await backend.close()

        backend._browser.close.assert_called_once()
        backend._playwright.stop.assert_called_once()


class TestPlaywrightBackendNewContext:
    @pytest.mark.asyncio
    async def test_creates_context_with_settings(self) -> None:
        config = YaReviewsConfig(browser_locale="en-US")
        backend = PlaywrightBackend(config)
        mock_browser = AsyncMock()
        mock_ctx = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_ctx)
        backend._browser = mock_browser

        ctx = await backend.new_context(
            locale="en-US",
            viewport={"width": 1280, "height": 720},
        )

        assert ctx is mock_ctx
        mock_browser.new_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_browser_not_started(self) -> None:
        config = YaReviewsConfig()
        backend = PlaywrightBackend(config)

        with pytest.raises(Exception, match="not started"):
            await backend.new_context()
