"""Tests for Pydantic models."""
from ya_reviews_mcp.reviews.models import CompanyInfo, Review, ReviewsResult


class TestReview:
    def test_full_review(self) -> None:
        r = Review(
            author_name="Alice",
            author_icon_url="https://example.com/icon.jpg",
            date="2025-01-15T12:00:00Z",
            text="Great place!",
            stars=5.0,
            business_response="Thank you!",
        )
        assert r.author_name == "Alice"
        assert r.stars == 5.0
        assert r.business_response == "Thank you!"

    def test_minimal_review(self) -> None:
        r = Review()
        assert r.author_name is None
        assert r.text is None
        assert r.stars == 0
        assert r.business_response is None

    def test_exclude_none(self) -> None:
        r = Review(author_name="Bob", text="OK", stars=3.0)
        data = r.model_dump(exclude_none=True)
        assert "author_icon_url" not in data
        assert "business_response" not in data
        assert data["author_name"] == "Bob"
        assert data["stars"] == 3.0


class TestCompanyInfo:
    def test_full_company(self) -> None:
        c = CompanyInfo(
            name="Test Cafe",
            rating=4.5,
            review_count=100,
            stars=4.5,
            address="Moscow, Red Square",
            categories=["Cafe", "Restaurant"],
        )
        assert c.name == "Test Cafe"
        assert c.review_count == 100
        assert len(c.categories) == 2

    def test_default_categories(self) -> None:
        c = CompanyInfo(name="Shop")
        assert c.categories == []


class TestReviewsResult:
    def test_serialization(self) -> None:
        result = ReviewsResult(
            company=CompanyInfo(name="Cafe", rating=4.0),
            reviews=[
                Review(author_name="Alice", stars=5.0),
                Review(author_name="Bob", stars=3.0),
            ],
            total_count=2,
        )
        data = result.model_dump()
        assert data["total_count"] == 2
        assert len(data["reviews"]) == 2
        assert data["company"]["name"] == "Cafe"
