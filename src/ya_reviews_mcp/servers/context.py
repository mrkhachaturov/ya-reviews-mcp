"""Request context dataclass for FastMCP lifespan."""
from dataclasses import dataclass

from ya_reviews_mcp.reviews.config import YaReviewsConfig
from ya_reviews_mcp.reviews.fetchers.fetcher import YaReviewsFetcher


@dataclass
class MainAppContext:
    fetcher: YaReviewsFetcher
    config: YaReviewsConfig
