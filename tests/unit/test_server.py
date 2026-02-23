"""Tests for the FastMCP server instance."""
from ya_reviews_mcp.servers.main import mcp


class TestServer:
    def test_server_name(self) -> None:
        assert mcp.name == "ya-reviews-mcp"

    def test_server_has_instructions(self) -> None:
        assert mcp.instructions is not None
        assert "org_id" in mcp.instructions
