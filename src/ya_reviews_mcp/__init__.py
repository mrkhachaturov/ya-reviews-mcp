"""ya-reviews-mcp: MCP server for Yandex Maps business reviews."""
from __future__ import annotations

import logging
from typing import Literal

import click
from dotenv import load_dotenv

from ya_reviews_mcp.utils.lifecycle import setup_signal_handlers
from ya_reviews_mcp.utils.logging import setup_logging

logger = logging.getLogger("ya-reviews")

TRANSPORTS = ["stdio", "streamable-http", "sse"]


@click.command()
@click.option(
    "--transport", default="stdio",
    type=click.Choice(TRANSPORTS), help="Transport mode",
)
@click.option("--port", default=8000, type=int, help="HTTP port")
@click.option("--host", default="0.0.0.0", help="HTTP host")
@click.option("--env-file", default=None, help="Path to .env file")
@click.option(
    "-v", "--verbose", count=True,
    help="Verbose logging (-v INFO, -vv DEBUG)",
)
def main(
    transport: str,
    port: int,
    host: str,
    env_file: str | None,
    verbose: int,
) -> None:
    """ya-reviews-mcp: Yandex Maps reviews MCP server."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    setup_logging(verbose)
    setup_signal_handlers()

    # Import tools to register them with the mcp instance
    import ya_reviews_mcp.servers.tools  # noqa: F401
    from ya_reviews_mcp.servers.main import mcp

    logger.info("Starting ya-reviews-mcp (transport=%s)", transport)

    transport_literal: Literal[
        "stdio", "streamable-http", "sse"
    ] = transport  # type: ignore[assignment]

    if transport_literal == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=transport_literal, host=host, port=port)


if __name__ == "__main__":
    main()
