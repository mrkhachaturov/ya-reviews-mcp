"""Base fetcher class for reviews."""
from __future__ import annotations

import json
from typing import Any

from ya_reviews_mcp.reviews.scraper import YaReviewsScraper


class BaseFetcher:
    def __init__(self, scraper: YaReviewsScraper) -> None:
        self.scraper = scraper

    def format_response(self, data: dict[str, Any] | list[Any]) -> str:
        """Format response as pretty-printed JSON string."""
        return json.dumps(data, ensure_ascii=False, indent=2)
