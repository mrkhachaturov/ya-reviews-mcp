"""Tests for ReviewsMixin via YaReviewsFetcher."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from ya_reviews_mcp.reviews.fetchers.fetcher import YaReviewsFetcher
from ya_reviews_mcp.reviews.models import CompanyInfo, Review, ReviewsResult


@pytest.fixture
def mock_scraper() -> MagicMock:
    scraper = MagicMock()
    scraper.fetch_reviews = AsyncMock(return_value=ReviewsResult(
        company=CompanyInfo(
            name="Test Cafe",
            rating=4.5,
            review_count=100,
            stars=4.5,
            address="Moscow, Red Square",
            categories=["Cafe"],
        ),
        reviews=[
            Review(
                author_name="Alice",
                text="Great place!",
                stars=5.0,
                date="2025-01-15T12:00:00Z",
                business_response="Thank you!",
            ),
            Review(
                author_name="Bob",
                text="Not bad",
                stars=3.0,
                date="2025-01-10T08:30:00Z",
            ),
        ],
        total_count=100,
    ))
    return scraper


@pytest.fixture
def fetcher(mock_scraper: MagicMock) -> YaReviewsFetcher:
    return YaReviewsFetcher(mock_scraper)


class TestGetReviews:
    async def test_returns_all_reviews(self, fetcher: YaReviewsFetcher) -> None:
        result = json.loads(await fetcher.get_reviews("12345"))
        assert result["org_id"] == "12345"
        assert result["total_count"] == 100
        assert result["returned_count"] == 2
        assert len(result["reviews"]) == 2

    async def test_max_reviews_truncates(self, fetcher: YaReviewsFetcher) -> None:
        result = json.loads(await fetcher.get_reviews("12345", max_reviews=1))
        assert result["returned_count"] == 1
        assert len(result["reviews"]) == 1
        assert result["reviews"][0]["author_name"] == "Alice"

    async def test_sort_passed_to_scraper(
        self, fetcher: YaReviewsFetcher, mock_scraper: MagicMock
    ) -> None:
        await fetcher.get_reviews("12345", sort="by_rating")
        mock_scraper.fetch_reviews.assert_called_with(
            org_id="12345", sort="by_rating"
        )


class TestGetCompanyInfo:
    async def test_returns_company_data(self, fetcher: YaReviewsFetcher) -> None:
        result = json.loads(await fetcher.get_company_info("12345"))
        assert result["org_id"] == "12345"
        assert result["company"]["name"] == "Test Cafe"
        assert result["company"]["rating"] == 4.5
        assert "reviews" not in result

    async def test_max_pages_one(
        self, fetcher: YaReviewsFetcher, mock_scraper: MagicMock
    ) -> None:
        await fetcher.get_company_info("12345")
        mock_scraper.fetch_reviews.assert_called_with(
            org_id="12345", max_pages=1
        )


class TestGetCompanySummary:
    async def test_returns_company_and_reviews(
        self, fetcher: YaReviewsFetcher
    ) -> None:
        result = json.loads(await fetcher.get_company_summary("12345"))
        assert result["org_id"] == "12345"
        assert result["company"]["name"] == "Test Cafe"
        assert result["total_reviews"] == 100
        assert len(result["recent_reviews"]) == 2

    async def test_max_reviews_limit(self, fetcher: YaReviewsFetcher) -> None:
        result = json.loads(await fetcher.get_company_summary("12345", max_reviews=1))
        assert len(result["recent_reviews"]) == 1
