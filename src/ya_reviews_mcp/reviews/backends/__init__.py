"""Browser backend abstraction layer."""
from __future__ import annotations

from enum import Enum

from ya_reviews_mcp.reviews.backends.base import BaseBrowserBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig


class BackendType(Enum):
    PLAYWRIGHT = "playwright"
    PATCHRIGHT = "patchright"
    REMOTE = "remote"


def create_backend(config: YaReviewsConfig) -> BaseBrowserBackend:
    """Create a browser backend based on config."""
    try:
        backend_type = BackendType(config.backend)
    except ValueError:
        raise ValueError(
            f"Unknown backend: {config.backend!r}. "
            f"Choose from: {', '.join(b.value for b in BackendType)}"
        )

    if backend_type == BackendType.PLAYWRIGHT:
        from ya_reviews_mcp.reviews.backends.playwright_backend import (
            PlaywrightBackend,
        )
        return PlaywrightBackend(config)

    if backend_type == BackendType.PATCHRIGHT:
        from ya_reviews_mcp.reviews.backends.patchright_backend import (
            PatchrightBackend,
        )
        return PatchrightBackend(config)

    # BackendType.REMOTE
    from ya_reviews_mcp.reviews.backends.remote_backend import RemoteCDPBackend
    return RemoteCDPBackend(config)
