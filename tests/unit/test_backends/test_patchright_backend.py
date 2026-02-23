"""Tests for PatchrightBackend."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ya_reviews_mcp.reviews.backends.patchright_backend import PatchrightBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig


class TestPatchrightBackendStartClose:
    @pytest.mark.asyncio
    async def test_start_launches_chromium(self) -> None:
        config = YaReviewsConfig()
        backend = PatchrightBackend(config)

        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch(
            "ya_reviews_mcp.reviews.backends.patchright_backend._import_patchright"
        ) as mock_import:
            mock_async_pw = MagicMock()
            mock_async_pw.return_value.start = AsyncMock(return_value=mock_pw)
            mock_import.return_value = mock_async_pw
            await backend.start()

        mock_pw.chromium.launch.assert_called_once()
        assert backend._browser is mock_browser

    @pytest.mark.asyncio
    async def test_close_stops_browser_and_patchright(self) -> None:
        config = YaReviewsConfig()
        backend = PatchrightBackend(config)
        backend._browser = AsyncMock()
        backend._playwright = AsyncMock()

        await backend.close()

        backend._browser.close.assert_called_once()
        backend._playwright.stop.assert_called_once()


class TestPatchrightBackendNewContext:
    @pytest.mark.asyncio
    async def test_raises_when_browser_not_started(self) -> None:
        config = YaReviewsConfig()
        backend = PatchrightBackend(config)

        with pytest.raises(Exception, match="not started"):
            await backend.new_context()


class TestPatchrightImportError:
    @pytest.mark.asyncio
    async def test_raises_helpful_error_when_not_installed(self) -> None:
        config = YaReviewsConfig()
        backend = PatchrightBackend(config)

        with patch(
            "ya_reviews_mcp.reviews.backends.patchright_backend._import_patchright",
            side_effect=Exception("Patchright is not installed"),
        ):
            with pytest.raises(Exception, match="Patchright is not installed"):
                await backend.start()
