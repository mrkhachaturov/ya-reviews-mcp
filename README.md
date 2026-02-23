# ya-reviews-mcp

![License](https://img.shields.io/github/license/mrkhachaturov/ya-reviews-mcp)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastMCP](https://img.shields.io/badge/FastMCP-2.13%2B-green)

Model Context Protocol (MCP) server for [Yandex Maps](https://yandex.ru/maps/) business reviews. Scrapes reviews from any Yandex Maps organization page and exposes them to your AI assistant — review text, ratings, author info, likes/dislikes, business responses, and company metadata.

No API key required. Uses a headless Chromium browser under the hood. Supports multiple browser backends: [Playwright](https://playwright.dev/), [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) (anti-detection), or a remote browser via CDP.

## Quick Start

### 1. Install

Choose your backend:

```bash
# Option A: Playwright (default)
pip install ya-reviews-mcp[playwright]
playwright install chromium

# Option B: Patchright (better anti-detection)
pip install ya-reviews-mcp[patchright]
patchright install chromium

# Option C: Remote browser (no local browser needed)
pip install ya-reviews-mcp
# Then run a browser separately, e.g.:
# docker run -p 3000:3000 ghcr.io/browserless/chromium
```

### 2. Find the Organization ID

Open any business on [Yandex Maps](https://yandex.ru/maps/) and look at the URL:

```
https://yandex.ru/maps/org/astra_motors/1248139252/reviews/
                                        ^^^^^^^^^^
                                        this is the org_id
```

### 3. Configure Your IDE

Add to your Claude Desktop / Cursor MCP configuration:

```json
{
  "mcpServers": {
    "ya-reviews": {
      "command": "uvx",
      "args": ["--from", "ya-reviews-mcp[playwright]", "ya-reviews-mcp"]
    }
  }
}
```

> **Using Patchright?** Replace `ya-reviews-mcp[playwright]` with `ya-reviews-mcp[patchright]` and add `"--backend", "patchright"` to args.

> **Running from source?** Use `uv run` instead:
> ```json
> {
>   "mcpServers": {
>     "ya-reviews": {
>       "command": "uv",
>       "args": ["run", "--directory", "/path/to/ya-reviews-mcp", "ya-reviews-mcp"]
>     }
>   }
> }
> ```

### 4. Start Using

Ask your AI assistant to:
- **"Get reviews for organization 1248139252"** — fetch all reviews with text, ratings, and business responses
- **"Show me company info for org 1248139252"** — company name, rating, review count
- **"Give me a summary of org 1248139252 with the last 10 reviews"** — company info + recent reviews in one call

## Tools

3 tools for Yandex Maps review data:

| Tool | Description |
|------|-------------|
| `get_reviews` | Fetch reviews with text, author, date, rating, likes/dislikes, direct review URL, and business responses. Supports `max_reviews` limit and `sort` (by_time or by_rating). |
| `get_company_info` | Company metadata: name, rating, review count, address, categories. |
| `get_company_summary` | Company info + recent reviews in one call. Best for a quick business overview. |

### Review Data Fields

Each review includes:

| Field | Description |
|-------|-------------|
| `author_name` | Reviewer's display name |
| `author_icon_url` | Avatar image URL |
| `author_profile_url` | Link to the reviewer's Yandex Maps profile |
| `date` | ISO 8601 date string |
| `text` | Full review text |
| `stars` | Rating (1.0 - 5.0) |
| `likes` | Thumbs up count |
| `dislikes` | Thumbs down count |
| `review_url` | Direct link to this specific review |
| `business_response` | Organization's reply text (if any) |

### Company Info Fields

| Field | Description |
|-------|-------------|
| `name` | Business name |
| `rating` | Overall rating (e.g., 4.8) |
| `review_count` | Total number of reviews |
| `address` | Business address |
| `categories` | Business categories list |

## Configuration

All configuration via environment variables (no API key needed):

| Variable | Default | Description |
|----------|---------|-------------|
| `BROWSER_BACKEND` | `playwright` | Browser backend: `playwright`, `patchright`, or `remote` |
| `BROWSER_WS_URL` | — | WebSocket URL for remote backend (e.g., `ws://localhost:3000`) |
| `BROWSER_HEADLESS` | `true` | Set to `false` for visual debugging |
| `PAGE_TIMEOUT` | `30000` | Page load timeout in ms |
| `INTERCEPT_TIMEOUT` | `15000` | Max wait for reviews to appear in DOM (ms) |
| `REQUEST_DELAY` | `2.0` | Delay between scroll loads (seconds) |
| `MAX_PAGES` | `20` | Max scroll iterations (50 reviews per scroll) |
| `SCRAPER_RETRIES` | `3` | Retry attempts for page loads |
| `SCRAPER_RETRY_DELAY` | `2.0` | Base delay between retries (seconds) |
| `BROWSER_LOCALE` | `ru-RU` | Browser locale |
| `ENABLED_TOOLS` | all | Comma-separated list of allowed tools |

Copy `.env.example` to `.env` and uncomment the values you want to change.

## CLI

```bash
# stdio (default, for MCP clients)
ya-reviews-mcp

# HTTP transport
ya-reviews-mcp --transport streamable-http --port 8000

# With verbose logging
ya-reviews-mcp -vv

# Use Patchright backend
ya-reviews-mcp --backend patchright

# Use remote browser
ya-reviews-mcp --backend remote --browser-url ws://localhost:3000

# Load custom .env file
ya-reviews-mcp --env-file /path/to/.env
```

## Installation

**From PyPI (with Playwright):**
```bash
pip install ya-reviews-mcp[playwright]
playwright install chromium
```

**From PyPI (with Patchright):**
```bash
pip install ya-reviews-mcp[patchright]
patchright install chromium
```

**From PyPI (remote browser only):**
```bash
pip install ya-reviews-mcp
```

**From source:**
```bash
git clone https://github.com/mrkhachaturov/ya-reviews-mcp
cd ya-reviews-mcp
uv sync --extra playwright
uv run playwright install chromium
uv run ya-reviews-mcp
```

## How It Works

Unlike `ya-metrics-mcp` which uses the official Yandex Metrika API, Yandex Maps has no public API for reviews. This server uses a headless browser to:

1. Navigate to the organization's reviews page on `yandex.ru/maps`
2. Parse review data from the server-rendered DOM (schema.org structured data)
3. Scroll to load additional reviews (50 per scroll, infinite pagination)
4. Click "Show organization response" buttons to reveal business replies
5. Extract all fields including likes/dislikes and direct review URLs

A single Chromium browser instance is shared across requests via FastMCP's lifespan context. Each scrape creates a fresh browser context (isolated cookies/state).

## Development

```bash
# Install with dev dependencies (includes playwright)
uv sync --extra dev

# Install browser
uv run playwright install chromium

# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## License

MIT
