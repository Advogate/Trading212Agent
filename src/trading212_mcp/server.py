"""Trading 212 MCP server entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from trading212_mcp.client import Trading212Client
from trading212_mcp.config import Settings
from trading212_mcp.tools.account import register_account_tools
from trading212_mcp.tools.history import register_history_tools
from trading212_mcp.tools.metadata import register_metadata_tools
from trading212_mcp.tools.portfolio import register_portfolio_tools

ClientFactory = Callable[[], AsyncIterator[Trading212Client]]


def create_server(settings: Settings | None = None) -> FastMCP:
    """Create the MCP server with the read-only Trading 212 toolset."""

    app_settings = settings or Settings()
    server = FastMCP(
        name="trading212",
        instructions=(
            "Read-only Trading 212 MCP server backed by the official Public API v0 docs. "
            "Use Basic auth with API key and secret, and prefer demo before live trading."
        ),
    )

    @asynccontextmanager
    async def client_factory() -> AsyncIterator[Trading212Client]:
        async with Trading212Client(app_settings) as client:
            yield client

    register_account_tools(server, client_factory)
    register_portfolio_tools(server, client_factory)
    register_metadata_tools(server, client_factory)
    register_history_tools(server, client_factory)
    return server


def main() -> None:
    """Run the MCP server over stdio."""

    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
