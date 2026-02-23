"""Tests for BaseBrowserBackend ABC."""
from ya_reviews_mcp.reviews.backends.base import BaseBrowserBackend


class TestBaseBrowserBackendIsAbstract:
    def test_cannot_instantiate(self) -> None:
        """ABC cannot be instantiated directly."""
        import pytest
        with pytest.raises(TypeError):
            BaseBrowserBackend()  # type: ignore[abstract]
