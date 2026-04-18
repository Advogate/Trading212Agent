"""Portfolio-focused MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from mcp.server.fastmcp import FastMCP

from trading212_mcp.client import Trading212Client
from trading212_mcp.models import UpstreamPayload

ClientFactory = Callable[[], AbstractAsyncContextManager[Trading212Client]]


def register_portfolio_tools(server: FastMCP, client_factory: ClientFactory) -> None:
    """Register portfolio and holdings tools."""

    @server.tool()
    async def list_positions(ticker: str | None = None) -> UpstreamPayload:
        """Return open positions, optionally filtered by Trading 212 ticker."""

        async with client_factory() as client:
            return UpstreamPayload(data=await client.list_positions(ticker=ticker))
