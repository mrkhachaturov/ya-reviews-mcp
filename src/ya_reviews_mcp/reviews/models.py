"""Pydantic models for Yandex Maps reviews data."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Review(BaseModel):
    """A single review from Yandex Maps."""

    author_name: str | None = None
    author_icon_url: str | None = None
    author_profile_url: str | None = None
    date: str | None = Field(None, description="ISO 8601 date string")
    text: str | None = None
    stars: float = 0
    likes: int = 0
    dislikes: int = 0
    review_url: str | None = None
    business_response: str | None = None


class CompanyInfo(BaseModel):
    """Company metadata from Yandex Maps."""

    name: str | None = None
    rating: float | None = None
    review_count: int | None = None
    stars: float | None = None
    address: str | None = None
    categories: list[str] = Field(default_factory=list)


class ReviewsResult(BaseModel):
    """Combined company info and reviews."""

    company: CompanyInfo
    reviews: list[Review]
    total_count: int
