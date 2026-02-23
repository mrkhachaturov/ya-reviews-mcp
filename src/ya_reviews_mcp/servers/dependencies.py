"""Dependency injection helpers for tool handlers."""
from fastmcp import Context

from ya_reviews_mcp.reviews.fetchers.fetcher import YaReviewsFetcher
from ya_reviews_mcp.servers.context import MainAppContext


async def get_reviews_fetcher(ctx: Context) -> YaReviewsFetcher:
    """Retrieve the shared YaReviewsFetcher from lifespan context."""
    req_ctx = ctx.request_context
    assert req_ctx is not None, "No request context"
    app_ctx: MainAppContext = req_ctx.lifespan_context
    return app_ctx.fetcher
