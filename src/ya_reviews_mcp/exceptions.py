"""Custom exceptions for ya-reviews-mcp."""


class MCPYaReviewsError(Exception):
    """Base exception for all ya-reviews-mcp errors."""


class ScrapingError(MCPYaReviewsError):
    """Raised when page scraping or network interception fails."""


class PageNotFoundError(MCPYaReviewsError):
    """Raised when the business page does not exist on Yandex Maps."""


class BrowserError(MCPYaReviewsError):
    """Raised when browser initialization or operation fails."""
