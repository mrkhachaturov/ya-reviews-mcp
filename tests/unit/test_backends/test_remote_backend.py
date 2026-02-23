"""Tests for RemoteCDPBackend."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ya_reviews_mcp.reviews.backends.remote_backend import RemoteCDPBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig


class TestRemoteCDPBackendStartClose:
    @pytest.mark.asyncio
    async def test_start_connects_via_cdp(self) -> None:
        config = YaReviewsConfig(browser_ws_url="ws://localhost:3000")
        backend = RemoteCDPBackend(config)

        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_pw.chromium.connect_over_cdp = AsyncMock(
            return_value=mock_browser,
        )

        with patch(
            "ya_reviews_mcp.reviews.backends.remote_backend.async_playwright"
        ) as mock_apw:
            mock_apw.return_value.start = AsyncMock(return_value=mock_pw)
            await backend.start()

        mock_pw.chromium.connect_over_cdp.assert_called_once_with(
            "ws://localhost:3000"
        )

    @pytest.mark.asyncio
    async def test_start_raises_without_ws_url(self) -> None:
        config = YaReviewsConfig(browser_ws_url=None)
        backend = RemoteCDPBackend(config)

        with pytest.raises(Exception, match="BROWSER_WS_URL"):
            await backend.start()

    @pytest.mark.asyncio
    async def test_close_disconnects(self) -> None:
        config = YaReviewsConfig(browser_ws_url="ws://localhost:3000")
        backend = RemoteCDPBackend(config)
        backend._browser = AsyncMock()
        backend._playwright = AsyncMock()

        await backend.close()

        backend._browser.close.assert_called_once()
        backend._playwright.stop.assert_called_once()
