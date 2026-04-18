"""Metadata-focused MCP tools backed by the official Trading 212 endpoints."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from mcp.server.fastmcp import FastMCP

from trading212_mcp.client import Trading212Client
from trading212_mcp.models import UpstreamPayload

ClientFactory = Callable[[], AbstractAsyncContextManager[Trading212Client]]


def register_metadata_tools(server: FastMCP, client_factory: ClientFactory) -> None:
    """Register metadata tools from the official instruments docs."""

    @server.tool()
    async def list_exchanges() -> UpstreamPayload:
        """Return exchange metadata from Trading 212."""

        async with client_factory() as client:
            return UpstreamPayload(data=await client.list_exchanges())

    @server.tool()
    async def list_instruments() -> UpstreamPayload:
        """Return the full accessible instrument metadata list from Trading 212."""

        async with client_factory() as client:
            return UpstreamPayload(data=await client.list_instruments())