"""Composite fetcher combining all domain mixins."""
from ya_reviews_mcp.reviews.fetchers.base import BaseFetcher
from ya_reviews_mcp.reviews.fetchers.reviews import ReviewsMixin


class YaReviewsFetcher(ReviewsMixin, BaseFetcher):
    """Full Yandex Maps reviews fetcher with all capabilities."""
