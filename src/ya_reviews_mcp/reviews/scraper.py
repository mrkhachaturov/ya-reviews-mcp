"""Backend-driven scraper for Yandex Maps reviews via DOM parsing."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from playwright.async_api import Page

from ya_reviews_mcp.exceptions import (
    PageNotFoundError,
    ScrapingError,
)
from ya_reviews_mcp.reviews.backends.base import BaseBrowserBackend
from ya_reviews_mcp.reviews.config import YaReviewsConfig
from ya_reviews_mcp.reviews.models import (
    CompanyInfo,
    Review,
    ReviewsResult,
)

logger = logging.getLogger("ya-reviews")

REVIEWS_URL_TEMPLATE = "https://yandex.ru/maps/org/{org_id}/reviews/"
REVIEW_URL_TEMPLATE = (
    "https://yandex.ru/maps/org/{org_id}/reviews"
    "?reviews%5BpublicId%5D={public_id}&utm_source=review"
)

# CSS selectors for DOM parsing
SEL_REVIEW = ".business-reviews-card-view__review"
SEL_AUTHOR_NAME = "[itemprop='name']"
SEL_DATE = "meta[itemprop='datePublished']"
SEL_RATING = "meta[itemprop='ratingValue']"
SEL_RATING_STARS = (
    ".business-rating-badge-view__stars._spacing_normal > span"
)
SEL_TEXT = ".business-review-view__body"
SEL_AVATAR = ".user-icon-view__icon"
SEL_BIZ_COMMENT_EXPAND = ".business-review-view__comment-expand"
SEL_BIZ_COMMENT_TEXT = ".business-review-comment-content__bubble"

# Company info selectors
SEL_COMPANY_NAME = "h1.orgpage-header-view__header"
SEL_COMPANY_RATING = ".business-summary-rating-badge-view__rating"
SEL_COMPANY_REVIEW_COUNT = "meta[itemprop='reviewCount']"
SEL_COMPANY_ADDRESS = "[class*='business-contacts-view__address-link']"
SEL_COMPANY_CATEGORIES = ".business-categories-view__category"


class YaReviewsScraper:
    """Manages browser via backend and parses Yandex Maps reviews from DOM."""

    def __init__(
        self,
        config: YaReviewsConfig,
        backend: BaseBrowserBackend,
    ) -> None:
        self.config = config
        self._backend = backend

    async def start(self) -> None:
        """Launch browser via backend. Called once from lifespan."""
        await self._backend.start()

    async def close(self) -> None:
        """Shut down browser via backend. Called once from lifespan."""
        await self._backend.close()

    async def _new_context(self) -> Any:
        """Create a fresh browser context via backend."""
        return await self._backend.new_context(
            locale=self.config.browser_locale,
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

    async def fetch_reviews(
        self,
        org_id: str,
        max_pages: int | None = None,
        sort: str = "by_time",
    ) -> ReviewsResult:
        """Fetch reviews for a business by parsing DOM elements.

        Args:
            org_id: Yandex Maps organization ID.
            max_pages: Max scroll iterations (None = use config.max_pages).
            sort: Sort order — "by_time" or "by_rating".

        Returns:
            ReviewsResult with company info and all reviews.
        """
        pages_limit = max_pages if max_pages is not None else self.config.max_pages
        context = await self._new_context()

        try:
            page = await context.new_page()

            # Hide webdriver flag before navigation
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)

            url = REVIEWS_URL_TEMPLATE.format(org_id=org_id)

            # Navigate with retry
            await self._navigate_with_retry(page, url)

            # Check if page exists
            await self._check_page_exists(page, org_id)

            # Wait for reviews to render
            await self._wait_for_reviews(page)

            # Parse company info from DOM
            company_info = await self._parse_company_info_from_dom(page)

            # Determine total count from DOM
            total_count = company_info.review_count or 0

            # Parse initial reviews
            all_reviews = await self._parse_reviews_from_dom(page, org_id)
            logger.info(
                "org_id=%s total_count=%d initial_reviews=%d",
                org_id, total_count, len(all_reviews),
            )

            # Scroll to load more reviews (pagination)
            prev_count = len(all_reviews)
            for scroll_num in range(2, pages_limit + 1):
                await self._scroll_to_load_more(page)
                all_reviews = await self._parse_reviews_from_dom(page, org_id)
                new_count = len(all_reviews)
                if new_count <= prev_count:
                    logger.debug(
                        "No new reviews after scroll %d (%d total), stopping",
                        scroll_num, new_count,
                    )
                    break
                logger.debug(
                    "Scroll %d: %d → %d reviews",
                    scroll_num, prev_count, new_count,
                )
                prev_count = new_count

            return ReviewsResult(
                company=company_info,
                reviews=all_reviews,
                total_count=total_count if total_count else len(all_reviews),
            )
        finally:
            await context.close()

    async def _navigate_with_retry(self, page: Page, url: str) -> None:
        """Navigate to URL with retry logic for transient failures."""
        for attempt in range(1, self.config.retries + 1):
            try:
                await page.goto(
                    url,
                    timeout=self.config.page_timeout,
                    wait_until="domcontentloaded",
                )
                return
            except Exception as exc:
                if attempt < self.config.retries:
                    logger.warning(
                        "Navigation attempt %d/%d failed: %s",
                        attempt, self.config.retries, exc,
                    )
                    await asyncio.sleep(self.config.retry_delay * attempt)
                else:
                    raise ScrapingError(
                        f"Failed to load {url} after {attempt} attempts: {exc}"
                    ) from exc

    async def _check_page_exists(self, page: Page, org_id: str) -> None:
        """Verify the business page loaded successfully."""
        try:
            await page.wait_for_selector(
                "[class*='orgpage-header'], [class*='business-card']",
                timeout=10000,
            )
        except Exception as exc:
            title = await page.title()
            if "404" in title or "не найден" in title.lower():
                raise PageNotFoundError(
                    f"Business with org_id={org_id} not found"
                ) from exc
            logger.warning(
                "Could not verify page content for org_id=%s", org_id,
            )

    async def _wait_for_reviews(self, page: Page) -> None:
        """Wait for review elements to appear in the DOM."""
        try:
            await page.wait_for_selector(
                SEL_REVIEW,
                timeout=self.config.intercept_timeout,
            )
        except Exception:
            logger.warning("Reviews container did not appear in time")

    async def _parse_company_info_from_dom(self, page: Page) -> CompanyInfo:
        """Extract company info from the page DOM."""
        name = await self._get_text(page, SEL_COMPANY_NAME)

        # Rating from summary badge (text is like "Рейтинг 4,8")
        rating_text = await self._get_text(page, SEL_COMPANY_RATING)
        rating = self._extract_rating(rating_text)

        # Review count from meta tag
        review_count_str = await self._get_attr(
            page, SEL_COMPANY_REVIEW_COUNT, "content",
        )
        review_count = (
            int(review_count_str) if review_count_str else None
        )

        # Address
        address = await self._get_text(page, SEL_COMPANY_ADDRESS)

        # Categories
        categories: list[str] = []
        cat_els = await page.query_selector_all(SEL_COMPANY_CATEGORIES)
        for el in cat_els:
            text = await el.text_content()
            if text and text.strip():
                categories.append(text.strip())

        return CompanyInfo(
            name=name,
            rating=rating,
            review_count=review_count,
            stars=rating,
            address=address,
            categories=categories,
        )

    async def _expand_business_responses(self, page: Page) -> None:
        """Click all 'Посмотреть ответ организации' buttons via JS."""
        clicked: int = await page.evaluate("""
            () => {
                const btns = document.querySelectorAll(
                    '.business-review-view__comment-expand'
                );
                let count = 0;
                btns.forEach(btn => {
                    if (btn.textContent.includes('Посмотреть')) {
                        btn.click();
                        count++;
                    }
                });
                return count;
            }
        """)
        if clicked:
            logger.debug("Expanded %d business responses", clicked)
            await asyncio.sleep(2)

    async def _parse_reviews_from_dom(
        self, page: Page, org_id: str,
    ) -> list[Review]:
        """Extract reviews from all review elements in the DOM."""
        await self._expand_business_responses(page)
        review_els = await page.query_selector_all(SEL_REVIEW)
        logger.debug("Found %d review elements in DOM", len(review_els))

        reviews: list[Review] = []
        for el in review_els:
            # Author name
            name_el = await el.query_selector(SEL_AUTHOR_NAME)
            name_text = await name_el.text_content() if name_el else None
            author_name = name_text.strip() if name_text else None

            # Avatar URL from style attribute
            avatar_el = await el.query_selector(SEL_AVATAR)
            author_icon = await self._extract_avatar_url(avatar_el)

            # Author profile URL + direct review link
            profile_el = await el.query_selector(".business-review-view__link")
            author_profile = (
                await profile_el.get_attribute("href")
                if profile_el else None
            )
            review_url = self._build_review_url(org_id, author_profile)

            # Date from meta tag
            date_el = await el.query_selector(SEL_DATE)
            date = (
                await date_el.get_attribute("content")
                if date_el
                else None
            )

            # Rating — try meta tag first, then count stars
            rating_el = await el.query_selector(SEL_RATING)
            if rating_el:
                rating_str = await rating_el.get_attribute("content")
                stars = self._parse_float(rating_str) or 0.0
            else:
                stars = await self._count_stars(el)

            # Review text — prefer inner text container, fall back to body
            text_container = await el.query_selector(
                ".spoiler-view__text-container"
            )
            if not text_container:
                text_container = await el.query_selector(SEL_TEXT)
            raw_text = (
                await text_container.text_content()
                if text_container else None
            )
            text = raw_text.strip() if raw_text else None

            # Likes and dislikes
            likes, dislikes = await self._extract_reactions(el)

            # Business response
            biz_response = await self._extract_business_response(el)

            reviews.append(Review(
                author_name=author_name,
                author_icon_url=author_icon,
                author_profile_url=author_profile,
                date=date,
                text=text,
                stars=stars,
                likes=likes,
                dislikes=dislikes,
                review_url=review_url,
                business_response=biz_response,
            ))

        return reviews

    async def _scroll_to_load_more(self, page: Page) -> None:
        """Scroll to the last review element to trigger infinite scroll."""
        await page.evaluate("""
            () => {
                const reviews = document.querySelectorAll(
                    '.business-reviews-card-view__review'
                );
                if (reviews.length > 0) {
                    reviews[reviews.length - 1].scrollIntoView();
                } else {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            }
        """)
        await asyncio.sleep(self.config.request_delay)

    @staticmethod
    async def _extract_reactions(review_el: Any) -> tuple[int, int]:
        """Extract like and dislike counts from a review element."""
        containers = await review_el.query_selector_all(
            ".business-reactions-view__container"
        )
        likes = 0
        dislikes = 0
        for container in containers:
            label = await container.get_attribute("aria-label") or ""
            counter_el = await container.query_selector(
                ".business-reactions-view__counter"
            )
            count_text = (
                await counter_el.text_content() if counter_el else "0"
            )
            try:
                count = int(count_text) if count_text else 0
            except ValueError:
                count = 0
            if "Лайк" in label:
                likes = count
            elif "Дизлайк" in label:
                dislikes = count
        return likes, dislikes

    @staticmethod
    async def _extract_avatar_url(avatar_el: Any) -> str | None:
        """Extract avatar URL from the style attribute background-image."""
        if not avatar_el:
            return None
        style = await avatar_el.get_attribute("style")
        if not style:
            return None
        # Parse background-image: url("...")
        match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
        return match.group(1) if match else None

    @staticmethod
    async def _count_stars(review_el: Any) -> float:
        """Count star rating by inspecting star span elements."""
        star_els = await review_el.query_selector_all(
            ".business-rating-badge-view__stars span"
        )
        rating = 0.0
        for star in star_els:
            cls = await star.get_attribute("class") or ""
            if "_empty" in cls:
                continue
            elif "_half" in cls:
                rating += 0.5
            else:
                rating += 1.0
        return rating

    @staticmethod
    async def _extract_business_response(review_el: Any) -> str | None:
        """Extract business response text from a review element."""
        # Try direct bubble text first
        bubble = await review_el.query_selector(SEL_BIZ_COMMENT_TEXT)
        if bubble:
            text = await bubble.text_content()
            return text.strip() if text else None
        return None

    @staticmethod
    async def _get_text(page: Page, selector: str) -> str | None:
        """Get trimmed text content from first matching element."""
        el = await page.query_selector(selector)
        if not el:
            return None
        text = await el.text_content()
        return text.strip() if text else None

    @staticmethod
    async def _get_attr(
        page: Page, selector: str, attr: str,
    ) -> str | None:
        """Get an attribute from the first matching element."""
        el = await page.query_selector(selector)
        if not el:
            return None
        return await el.get_attribute(attr)

    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        """Safely parse a float from a string."""
        if not value:
            return None
        try:
            return float(value.replace(",", "."))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _extract_rating(text: str | None) -> float | None:
        """Extract a rating number from text like 'Рейтинг 4,8'."""
        if not text:
            return None
        match = re.search(r"(\d+[.,]\d+|\d+)", text)
        if match:
            return float(match.group(1).replace(",", "."))
        return None

    @staticmethod
    def _build_review_url(
        org_id: str, profile_url: str | None,
    ) -> str | None:
        """Build a direct review URL from org_id and author profile URL.

        Profile URL format: https://yandex.ru/maps/user/{publicId}
        Review URL format:  https://yandex.ru/maps/org/{org_id}/reviews
                            ?reviews[publicId]={publicId}&utm_source=review
        """
        if not profile_url:
            return None
        # Extract publicId — last path segment of the profile URL
        public_id = profile_url.rstrip("/").rsplit("/", 1)[-1]
        if not public_id:
            return None
        return REVIEW_URL_TEMPLATE.format(
            org_id=org_id, public_id=public_id,
        )
