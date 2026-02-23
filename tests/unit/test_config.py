"""Tests for YaReviewsConfig."""

import pytest

from ya_reviews_mcp.reviews.config import YaReviewsConfig


class TestYaReviewsConfig:
    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BROWSER_HEADLESS", raising=False)
        monkeypatch.delenv("PAGE_TIMEOUT", raising=False)
        monkeypatch.delenv("INTERCEPT_TIMEOUT", raising=False)
        monkeypatch.delenv("REQUEST_DELAY", raising=False)
        monkeypatch.delenv("MAX_PAGES", raising=False)
        monkeypatch.delenv("SCRAPER_RETRIES", raising=False)
        monkeypatch.delenv("SCRAPER_RETRY_DELAY", raising=False)
        monkeypatch.delenv("BROWSER_LOCALE", raising=False)
        monkeypatch.delenv("ENABLED_TOOLS", raising=False)

        cfg = YaReviewsConfig.from_env()

        assert cfg.headless is True
        assert cfg.page_timeout == 30000
        assert cfg.intercept_timeout == 15000
        assert cfg.request_delay == 2.0
        assert cfg.max_pages == 20
        assert cfg.retries == 3
        assert cfg.retry_delay == 2.0
        assert cfg.browser_locale == "ru-RU"
        assert cfg.enabled_tools is None

    def test_custom_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BROWSER_HEADLESS", "false")
        monkeypatch.setenv("PAGE_TIMEOUT", "60000")
        monkeypatch.setenv("INTERCEPT_TIMEOUT", "20000")
        monkeypatch.setenv("REQUEST_DELAY", "3.5")
        monkeypatch.setenv("MAX_PAGES", "50")
        monkeypatch.setenv("SCRAPER_RETRIES", "5")
        monkeypatch.setenv("SCRAPER_RETRY_DELAY", "4.0")
        monkeypatch.setenv("BROWSER_LOCALE", "en-US")
        monkeypatch.setenv("ENABLED_TOOLS", "get_reviews, get_company_info")

        cfg = YaReviewsConfig.from_env()

        assert cfg.headless is False
        assert cfg.page_timeout == 60000
        assert cfg.intercept_timeout == 20000
        assert cfg.request_delay == 3.5
        assert cfg.max_pages == 50
        assert cfg.retries == 5
        assert cfg.retry_delay == 4.0
        assert cfg.browser_locale == "en-US"
        assert cfg.enabled_tools == ["get_reviews", "get_company_info"]

    def test_empty_enabled_tools(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENABLED_TOOLS", "  ")
        cfg = YaReviewsConfig.from_env()
        assert cfg.enabled_tools is None
