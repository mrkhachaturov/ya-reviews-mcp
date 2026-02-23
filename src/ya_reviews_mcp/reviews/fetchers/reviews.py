"""Reviews fetcher mixin."""
from __future__ import annotations

from ya_reviews_mcp.utils.decorators import handle_scraper_errors


class ReviewsMixin:
    """Mixin for Yandex Maps review operations.

    Requires self.scraper (YaReviewsScraper) and self.format_response()
    from BaseFetcher.
    """

    @handle_scraper_errors()
    async def get_reviews(
        self,
        org_id: str,
        max_reviews: int | None = None,
        sort: str = "by_time",
    ) -> str:
        """Fetch reviews for a business."""
        result = await self.scraper.fetch_reviews(  # type: ignore[attr-defined]
            org_id=org_id,
            sort=sort,
        )
        reviews_data = [
            r.model_dump(exclude_none=True) for r in result.reviews
        ]
        if max_reviews is not None:
            reviews_data = reviews_data[:max_reviews]
        return self.format_response({  # type: ignore[attr-defined, no-any-return]
            "org_id": org_id,
            "total_count": result.total_count,
            "returned_count": len(reviews_data),
            "reviews": reviews_data,
        })

    @handle_scraper_errors()
    async def get_company_info(self, org_id: str) -> str:
        """Fetch company metadata (loads first page to get info)."""
        result = await self.scraper.fetch_reviews(  # type: ignore[attr-defined]
            org_id=org_id,
            max_pages=1,
        )
        return self.format_response({  # type: ignore[attr-defined, no-any-return]
            "org_id": org_id,
            "company": result.company.model_dump(exclude_none=True),
        })

    @handle_scraper_errors()
    async def get_company_summary(
        self,
        org_id: str,
        max_reviews: int = 10,
    ) -> str:
        """Fetch company info + recent reviews in one call."""
        result = await self.scraper.fetch_reviews(  # type: ignore[attr-defined]
            org_id=org_id,
            max_pages=1,
            sort="by_time",
        )
        reviews_data = [
            r.model_dump(exclude_none=True)
            for r in result.reviews[:max_reviews]
        ]
        return self.format_response({  # type: ignore[attr-defined, no-any-return]
            "org_id": org_id,
            "company": result.company.model_dump(exclude_none=True),
            "total_reviews": result.total_count,
            "recent_reviews": reviews_data,
        })
