"""Tests for BaseFetcher."""
import json
from unittest.mock import MagicMock

from ya_reviews_mcp.reviews.fetchers.base import BaseFetcher


class TestBaseFetcher:
    def test_format_response_dict(self) -> None:
        scraper = MagicMock()
        fetcher = BaseFetcher(scraper)
        result = fetcher.format_response({"key": "value", "count": 42})
        parsed = json.loads(result)
        assert parsed == {"key": "value", "count": 42}

    def test_format_response_list(self) -> None:
        scraper = MagicMock()
        fetcher = BaseFetcher(scraper)
        result = fetcher.format_response([1, 2, 3])
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_format_response_cyrillic(self) -> None:
        scraper = MagicMock()
        fetcher = BaseFetcher(scraper)
        result = fetcher.format_response({"name": "Кафе Пушкин"})
        assert "Кафе Пушкин" in result
