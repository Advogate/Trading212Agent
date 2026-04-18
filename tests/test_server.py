from __future__ import annotations

import asyncio

from trading212_mcp.server import create_server


def test_server_registers_expected_tools() -> None:
    async def scenario() -> list[str]:
        server = create_server()
        tools = await server.list_tools()
        return sorted(tool.name for tool in tools)

    tool_names = asyncio.run(scenario())

    assert tool_names == [
        "get_account_summary",
        "list_dividends",
        "list_exchanges",
        "list_export_reports",
        "list_historical_orders",
        "list_instruments",
        "list_positions",
        "list_transactions",
    ]
