# ya-reviews-mcp

MCP server that scrapes Yandex Maps business reviews via Playwright headless browser.

## Commands

| Command | Description |
|---------|-------------|
| `uv sync --extra dev` | Install all dependencies (including dev) |
| `uv run playwright install chromium` | Install Chromium (required before first run) |
| `uv run ya-reviews-mcp` | Run server (stdio transport) |
| `uv run ya-reviews-mcp --transport streamable-http --port 8000` | Run with HTTP transport |
| `uv run pytest` | Run tests |
| `uv run ruff check src/` | Lint |
| `uv run ruff format src/` | Format |
| `uv run mypy src/` | Type check (strict mode) |

## Architecture

```
src/ya_reviews_mcp/
  __init__.py           # CLI entry point (Click command)
  exceptions.py         # Exception hierarchy: MCPYaReviewsError → Scraping/PageNotFound/Browser
  reviews/
    config.py           # YaReviewsConfig — env-based settings dataclass
    models.py           # Pydantic models: Review, CompanyInfo, ReviewsResult
    scraper.py          # YaReviewsScraper — Playwright browser + DOM parsing
    fetchers/
      base.py           # BaseFetcher — JSON response formatting
      reviews.py        # ReviewsMixin — business logic (get_reviews, get_company_info, get_company_summary)
      fetcher.py        # YaReviewsFetcher — composite of Base + ReviewsMixin
  servers/
    main.py             # FastMCP instance + lifespan (browser lifecycle)
    tools.py            # @mcp.tool registrations (3 tools)
    context.py          # MainAppContext dataclass
    dependencies.py     # Dependency injection helper
  utils/
    decorators.py       # handle_scraper_errors decorator
    lifecycle.py        # Signal handlers (SIGTERM/SIGINT)
    logging.py          # Verbosity-based logging setup
```

## MCP Tools

- `get_reviews(org_id, max_reviews?, sort?)` — fetch paginated reviews
- `get_company_info(org_id)` — company metadata (name, rating, address, categories)
- `get_company_summary(org_id, max_reviews?)` — company info + recent reviews in one call

## Code Style

- Python 3.10+, strict mypy
- Ruff: line-length 88, rules E/F/B/W/I/N/UP
- Async/await everywhere — Playwright requires it
- Pydantic v2 models for data, dataclasses for config
- Mixin pattern for fetchers (BaseFetcher + ReviewsMixin → YaReviewsFetcher)

## Gotchas

- **Do NOT use `from __future__ import annotations` in `servers/tools.py`** — FastMCP evaluates `Annotated[...]` at decoration time and needs real types
- Chromium must be installed separately (`uv run playwright install chromium`) before the server can start
- The scraper uses DOM CSS selectors, not an API — Yandex Maps DOM changes can break parsing
- Single browser instance is shared across requests; each request gets a fresh context for cookie isolation
- Anti-detection measures: webdriver flag hidden, realistic user-agent, automation flags disabled
- First request is slower (browser page load); subsequent requests reuse the browser

## Environment

All optional. Set via `.env` file or environment variables (see `.env.example`):

- `BROWSER_HEADLESS` — `true`/`false` (default: true)
- `PAGE_TIMEOUT` — page load timeout in ms (default: 30000)
- `INTERCEPT_TIMEOUT` — wait for reviews DOM in ms (default: 15000)
- `REQUEST_DELAY` — delay between scroll pagination in seconds (default: 2.0)
- `MAX_PAGES` — max review pages to fetch (default: 20)
- `SCRAPER_RETRIES` / `SCRAPER_RETRY_DELAY` — retry config
- `BROWSER_LOCALE` — browser locale (default: ru-RU)
- `ENABLED_TOOLS` — comma-separated tool filter

## Testing

- `uv run pytest` — all tests
- `uv run pytest tests/unit/test_scraper.py` — single file
- Tests use mocks for Playwright elements (no real browser needed)
- pytest-asyncio with `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` needed
