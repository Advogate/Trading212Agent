"""Historical data MCP tools backed by the official Trading 212 endpoints."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from mcp.server.fastmcp import FastMCP

from trading212_mcp.client import Trading212Client
from trading212_mcp.models import UpstreamPayload

ClientFactory = Callable[[], AbstractAsyncContextManager[Trading212Client]]


def register_history_tools(server: FastMCP, client_factory: ClientFactory) -> None:
    """Register read-only historical data tools."""

    @server.tool()
    async def list_dividends(
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int = 20,
    ) -> UpstreamPayload:
        """Return dividend history using Trading 212 cursor pagination."""

        async with client_factory() as client:
            return UpstreamPayload(
                data=await client.list_dividends(cursor=cursor, ticker=ticker, limit=limit)
            )

    @server.tool()
    async def list_export_reports() -> UpstreamPayload:
        """Return the current CSV export report list from Trading 212."""

        async with client_factory() as client:
            return UpstreamPayload(data=await client.list_export_reports())

    @server.tool()
    async def list_historical_orders(
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int = 20,
    ) -> UpstreamPayload:
        """Return historical orders using Trading 212 cursor pagination."""

        async with client_factory() as client:
            return UpstreamPayload(
                data=await client.list_historical_orders(cursor=cursor, ticker=ticker, limit=limit)
            )

    @server.tool()
    async def list_transactions(
        cursor: str | None = None,
        time: str | None = None,
        limit: int = 20,
    ) -> UpstreamPayload:
        """Return transaction history using Trading 212 cursor pagination."""

        async with client_factory() as client:
            return UpstreamPayload(
                data=await client.list_transactions(cursor=cursor, time=time, limit=limit)
            )