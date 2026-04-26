from __future__ import annotations

import asyncio

from starlette.testclient import TestClient

from trading212_mcp.config import Settings
from trading212_mcp.errors import ConfigurationError
from trading212_mcp.server import create_http_app, create_server


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


def test_server_applies_http_settings() -> None:
    settings = Settings(
        _env_file=None,
        api_key="key",
        api_secret="secret",
        transport="streamable-http",
        host="0.0.0.0",
        port=9000,
        streamable_http_path="/trade",
    )

    server = create_server(settings)

    assert server.settings.host == "0.0.0.0"
    assert server.settings.port == 9000
    assert server.settings.streamable_http_path == "/trade"


def test_server_exposes_health_endpoint() -> None:
    settings = Settings(
        _env_file=None,
        api_key="key",
        api_secret="secret",
        transport="streamable-http",
        auth_token="token",
        streamable_http_path="/mcp",
    )

    with TestClient(create_http_app(settings)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "transport": "streamable-http",
        "streamable_http_path": "/mcp",
    }


def test_http_app_requires_bearer_token_for_mcp_path() -> None:
    settings = Settings(
        _env_file=None,
        api_key="key",
        api_secret="secret",
        auth_token="secret-token",
        streamable_http_path="/mcp",
    )

    with TestClient(create_http_app(settings)) as client:
        unauthorized = client.get("/mcp")
        authorized = client.get("/mcp", headers={"Authorization": "Bearer secret-token"})

    assert unauthorized.status_code == 401
    assert authorized.status_code != 401


def test_http_app_rate_limits_protected_path() -> None:
    settings = Settings(
        _env_file=None,
        api_key="key",
        api_secret="secret",
        auth_token="secret-token",
        streamable_http_path="/mcp",
        rate_limit_requests=2,
        rate_limit_window_seconds=60,
    )

    with TestClient(create_http_app(settings)) as client:
        headers = {"Authorization": "Bearer secret-token"}
        first = client.get("/mcp", headers=headers)
        second = client.get("/mcp", headers=headers)
        third = client.get("/mcp", headers=headers)

    assert first.status_code != 429
    assert second.status_code != 429
    assert third.status_code == 429


def test_http_app_requires_auth_token_when_enforced() -> None:
    settings = Settings(
        _env_file=None,
        api_key="key",
        api_secret="secret",
        enforce_http_bearer_auth=True,
    )

    try:
        create_http_app(settings)
    except ConfigurationError as exc:
        assert "T212_AUTH_TOKEN" in str(exc)
    else:
        raise AssertionError("Expected ConfigurationError")
