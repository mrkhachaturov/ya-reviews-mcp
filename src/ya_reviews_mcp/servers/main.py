"""FastMCP server setup with lifespan and browser backend lifecycle."""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from ya_reviews_mcp.reviews.backends import create_backend
from ya_reviews_mcp.reviews.config import YaReviewsConfig
from ya_reviews_mcp.reviews.fetchers.fetcher import YaReviewsFetcher
from ya_reviews_mcp.reviews.scraper import YaReviewsScraper
from ya_reviews_mcp.servers.context import MainAppContext

logger = logging.getLogger("ya-reviews")


@asynccontextmanager
async def main_lifespan(
    app: FastMCP[Any],
) -> AsyncIterator[MainAppContext]:
    """Initialize and clean up the browser backend on server start/stop."""
    config = YaReviewsConfig.from_env()
    logger.info(
        "Starting ya-reviews-mcp, backend=%s, headless=%s, enabled_tools=%s",
        config.backend,
        config.headless,
        config.enabled_tools,
    )
    backend = create_backend(config)
    scraper = YaReviewsScraper(config, backend)
    await scraper.start()
    fetcher = YaReviewsFetcher(scraper)
    try:
        yield MainAppContext(fetcher=fetcher, config=config)
    finally:
        await scraper.close()
        logger.info("ya-reviews-mcp shutdown complete")


mcp = FastMCP(
    name="ya-reviews-mcp",
    instructions=(
        "MCP server for Yandex Maps business reviews.\n\n"
        "## Typical workflow\n"
        "1. Get the Yandex Maps org ID from the business page URL "
        "(e.g., https://yandex.ru/maps/org/12345/).\n"
        "2. Call `get_company_summary` for a quick overview with recent reviews.\n"
        "3. Call `get_reviews` for full review data with pagination.\n"
        "4. Call `get_company_info` for metadata only (name, rating, count).\n\n"
        "## Parameters\n"
        "- `org_id`: The numeric organization ID from Yandex Maps.\n"
        "- `max_reviews`: Limit number of reviews returned (default: all available).\n"
        "- `sort`: Sort reviews by 'by_time' (newest first) or 'by_rating'.\n\n"
        "## Notes\n"
        "- First call may be slower as the browser loads the page.\n"
        "- Reviews are fetched via browser automation, not an official API.\n"
        "- Rate limiting is built in to avoid detection."
    ),
    lifespan=main_lifespan,
)
