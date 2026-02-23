"""Tests for backend factory."""
from __future__ import annotations

import pytest

from ya_reviews_mcp.reviews.backends import BackendType, create_backend
from ya_reviews_mcp.reviews.backends.playwright_backend import PlaywrightBackend
from ya_reviews_mcp.reviews.backends.patchright_backend import PatchrightBackend
from ya_reviews_mcp.reviews.backends.remote_backend import RemoteCDPBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig


class TestBackendType:
    def test_enum_values(self) -> None:
        assert BackendType.PLAYWRIGHT.value == "playwright"
        assert BackendType.PATCHRIGHT.value == "patchright"
        assert BackendType.REMOTE.value == "remote"


class TestCreateBackend:
    def test_creates_playwright_backend(self) -> None:
        config = YaReviewsConfig(backend="playwright")
        backend = create_backend(config)
        assert isinstance(backend, PlaywrightBackend)

    def test_creates_patchright_backend(self) -> None:
        config = YaReviewsConfig(backend="patchright")
        backend = create_backend(config)
        assert isinstance(backend, PatchrightBackend)

    def test_creates_remote_backend(self) -> None:
        config = YaReviewsConfig(backend="remote")
        backend = create_backend(config)
        assert isinstance(backend, RemoteCDPBackend)

    def test_raises_for_unknown_backend(self) -> None:
        config = YaReviewsConfig(backend="firefox")
        with pytest.raises(ValueError, match="Unknown backend"):
            create_backend(config)
