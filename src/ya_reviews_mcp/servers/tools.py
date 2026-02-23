"""MCP tool registrations for Yandex Maps reviews."""
from typing import Annotated, cast

from fastmcp import Context
from pydantic import Field

from ya_reviews_mcp.servers.dependencies import get_reviews_fetcher
from ya_reviews_mcp.servers.main import mcp

# NOTE: Do NOT use `from __future__ import annotations` here.
# FastMCP evaluates Annotated[...] at decoration time.

OrgId = Annotated[
    str, Field(description="Yandex Maps organization ID (numeric)")
]


@mcp.tool(tags={"reviews", "read"})
async def get_reviews(
    ctx: Context,
    org_id: OrgId,
    max_reviews: Annotated[
        int | None,
        Field(description="Max number of reviews to return"),
    ] = None,
    sort: Annotated[
        str,
        Field(description="Sort: 'by_time' or 'by_rating'"),
    ] = "by_time",
) -> str:
    """Fetch reviews for a Yandex Maps business.

    Returns review text, author, date, rating, and
    business responses.
    """
    fetcher = await get_reviews_fetcher(ctx)
    return cast(str, await fetcher.get_reviews(org_id, max_reviews, sort))


@mcp.tool(tags={"reviews", "read"})
async def get_company_info(
    ctx: Context,
    org_id: OrgId,
) -> str:
    """Get company metadata from Yandex Maps.

    Returns name, rating, review count, address, categories.
    """
    fetcher = await get_reviews_fetcher(ctx)
    return cast(str, await fetcher.get_company_info(org_id))


@mcp.tool(tags={"reviews", "read"})
async def get_company_summary(
    ctx: Context,
    org_id: OrgId,
    max_reviews: Annotated[
        int,
        Field(
            description="Recent reviews to include",
            ge=1,
            le=50,
        ),
    ] = 10,
) -> str:
    """Get company info plus recent reviews in one call.

    Best for a quick business overview.
    """
    fetcher = await get_reviews_fetcher(ctx)
    return cast(
        str, await fetcher.get_company_summary(org_id, max_reviews)
    )
