"""Tests for YaReviewsScraper utility and parsing methods."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ya_reviews_mcp.reviews.scraper import YaReviewsScraper


class TestExtractRating:
    def test_russian_format(self) -> None:
        assert YaReviewsScraper._extract_rating("Рейтинг 4,8") == 4.8

    def test_plain_number(self) -> None:
        assert YaReviewsScraper._extract_rating("4.5") == 4.5

    def test_integer(self) -> None:
        assert YaReviewsScraper._extract_rating("Рейтинг 5") == 5.0

    def test_none(self) -> None:
        assert YaReviewsScraper._extract_rating(None) is None

    def test_no_number(self) -> None:
        assert YaReviewsScraper._extract_rating("Рейтинг") is None


class TestBuildReviewUrl:
    def test_valid_profile(self) -> None:
        url = YaReviewsScraper._build_review_url(
            "1248139252",
            "https://yandex.ru/maps/user/7khx434nbxqb0nu1hnu1tcey4c",
        )
        assert url == (
            "https://yandex.ru/maps/org/1248139252/reviews"
            "?reviews%5BpublicId%5D=7khx434nbxqb0nu1hnu1tcey4c"
            "&utm_source=review"
        )

    def test_trailing_slash(self) -> None:
        url = YaReviewsScraper._build_review_url(
            "123", "https://yandex.ru/maps/user/abc123/",
        )
        assert url is not None
        assert "abc123" in url

    def test_none_profile(self) -> None:
        assert YaReviewsScraper._build_review_url("123", None) is None

    def test_empty_profile(self) -> None:
        assert YaReviewsScraper._build_review_url("123", "") is None


class TestParseFloat:
    def test_valid_float(self) -> None:
        assert YaReviewsScraper._parse_float("4.5") == 4.5

    def test_comma_decimal(self) -> None:
        assert YaReviewsScraper._parse_float("4,5") == 4.5

    def test_integer_string(self) -> None:
        assert YaReviewsScraper._parse_float("5") == 5.0

    def test_none(self) -> None:
        assert YaReviewsScraper._parse_float(None) is None

    def test_empty_string(self) -> None:
        assert YaReviewsScraper._parse_float("") is None

    def test_invalid_string(self) -> None:
        assert YaReviewsScraper._parse_float("abc") is None


class TestExtractAvatarUrl:
    @pytest.mark.asyncio
    async def test_with_url(self) -> None:
        el = AsyncMock()
        el.get_attribute = AsyncMock(
            return_value='background-image: url("https://example.com/pic.jpg")'
        )
        result = await YaReviewsScraper._extract_avatar_url(el)
        assert result == "https://example.com/pic.jpg"

    @pytest.mark.asyncio
    async def test_with_unquoted_url(self) -> None:
        el = AsyncMock()
        el.get_attribute = AsyncMock(
            return_value="background-image: url(https://example.com/pic.jpg)"
        )
        result = await YaReviewsScraper._extract_avatar_url(el)
        assert result == "https://example.com/pic.jpg"

    @pytest.mark.asyncio
    async def test_no_style(self) -> None:
        el = AsyncMock()
        el.get_attribute = AsyncMock(return_value=None)
        result = await YaReviewsScraper._extract_avatar_url(el)
        assert result is None

    @pytest.mark.asyncio
    async def test_none_element(self) -> None:
        result = await YaReviewsScraper._extract_avatar_url(None)
        assert result is None


class TestCountStars:
    @pytest.mark.asyncio
    async def test_five_full_stars(self) -> None:
        stars = []
        for _ in range(5):
            s = AsyncMock()
            s.get_attribute = AsyncMock(return_value="star")
            stars.append(s)
        review_el = AsyncMock()
        review_el.query_selector_all = AsyncMock(return_value=stars)
        result = await YaReviewsScraper._count_stars(review_el)
        assert result == 5.0

    @pytest.mark.asyncio
    async def test_three_and_half_stars(self) -> None:
        stars = []
        for _ in range(3):
            s = AsyncMock()
            s.get_attribute = AsyncMock(return_value="star")
            stars.append(s)
        half = AsyncMock()
        half.get_attribute = AsyncMock(return_value="star _half")
        stars.append(half)
        empty = AsyncMock()
        empty.get_attribute = AsyncMock(return_value="star _empty")
        stars.append(empty)
        review_el = AsyncMock()
        review_el.query_selector_all = AsyncMock(return_value=stars)
        result = await YaReviewsScraper._count_stars(review_el)
        assert result == 3.5

    @pytest.mark.asyncio
    async def test_no_stars(self) -> None:
        review_el = AsyncMock()
        review_el.query_selector_all = AsyncMock(return_value=[])
        result = await YaReviewsScraper._count_stars(review_el)
        assert result == 0.0


class TestExtractReactions:
    @pytest.mark.asyncio
    async def test_likes_and_dislikes(self) -> None:
        like_counter = AsyncMock()
        like_counter.text_content = AsyncMock(return_value="7")
        like_container = AsyncMock()
        like_container.get_attribute = AsyncMock(return_value="Лайк")
        like_container.query_selector = AsyncMock(return_value=like_counter)

        dislike_counter = AsyncMock()
        dislike_counter.text_content = AsyncMock(return_value="2")
        dislike_container = AsyncMock()
        dislike_container.get_attribute = AsyncMock(return_value="Дизлайк")
        dislike_container.query_selector = AsyncMock(return_value=dislike_counter)

        review_el = AsyncMock()
        review_el.query_selector_all = AsyncMock(
            return_value=[like_container, dislike_container]
        )
        likes, dislikes = await YaReviewsScraper._extract_reactions(review_el)
        assert likes == 7
        assert dislikes == 2

    @pytest.mark.asyncio
    async def test_no_reactions(self) -> None:
        review_el = AsyncMock()
        review_el.query_selector_all = AsyncMock(return_value=[])
        likes, dislikes = await YaReviewsScraper._extract_reactions(review_el)
        assert likes == 0
        assert dislikes == 0


class TestExtractBusinessResponse:
    @pytest.mark.asyncio
    async def test_with_bubble(self) -> None:
        bubble = AsyncMock()
        bubble.text_content = AsyncMock(return_value="Thank you!")
        review_el = AsyncMock()
        review_el.query_selector = AsyncMock(return_value=bubble)
        result = await YaReviewsScraper._extract_business_response(review_el)
        assert result == "Thank you!"

    @pytest.mark.asyncio
    async def test_no_response(self) -> None:
        review_el = AsyncMock()
        review_el.query_selector = AsyncMock(return_value=None)
        result = await YaReviewsScraper._extract_business_response(review_el)
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_text(self) -> None:
        bubble = AsyncMock()
        bubble.text_content = AsyncMock(return_value="")
        review_el = AsyncMock()
        review_el.query_selector = AsyncMock(return_value=bubble)
        result = await YaReviewsScraper._extract_business_response(review_el)
        assert result is None


class TestGetText:
    @pytest.mark.asyncio
    async def test_found(self) -> None:
        el = AsyncMock()
        el.text_content = AsyncMock(return_value="  Hello  ")
        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=el)
        result = await YaReviewsScraper._get_text(page, ".test")
        assert result == "Hello"

    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=None)
        result = await YaReviewsScraper._get_text(page, ".missing")
        assert result is None


class TestGetAttr:
    @pytest.mark.asyncio
    async def test_found(self) -> None:
        el = AsyncMock()
        el.get_attribute = AsyncMock(return_value="423")
        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=el)
        result = await YaReviewsScraper._get_attr(page, "meta", "content")
        assert result == "423"

    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        page = AsyncMock()
        page.query_selector = AsyncMock(return_value=None)
        result = await YaReviewsScraper._get_attr(page, "meta", "content")
        assert result is None
