"""Decorator utilities for error handling."""
from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any

from ya_reviews_mcp.exceptions import MCPYaReviewsError

logger = logging.getLogger("ya-reviews")


def handle_scraper_errors(
    service_name: str = "Yandex Maps Scraper",
) -> Callable[..., Any]:
    """Decorator that catches scraper errors and re-raises as MCPYaReviewsError."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except MCPYaReviewsError:
                raise
            except Exception as exc:
                logger.error(
                    "%s error in %s: %s",
                    service_name, func.__name__, exc,
                )
                raise MCPYaReviewsError(
                    f"{service_name} error in {func.__name__}: {exc}"
                ) from exc
        return wrapper
    return decorator
