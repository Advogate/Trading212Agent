"""Account-focused MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from mcp.server.fastmcp import FastMCP

from trading212_mcp.client import Trading212Client
from trading212_mcp.models import UpstreamPayload

ClientFactory = Callable[[], AbstractAsyncContextManager[Trading212Client]]


def register_account_tools(server: FastMCP, client_factory: ClientFactory) -> None:
    """Register account-level read-only tools."""

    @server.tool()
    async def get_account_summary() -> UpstreamPayload:
        """Return the configured Trading 212 account summary payload."""

        async with client_factory() as client:
            return UpstreamPayload(data=await client.get_account_summary())
