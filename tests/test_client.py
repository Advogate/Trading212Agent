from __future__ import annotations

import asyncio
import base64
import json

import httpx

from trading212_mcp.client import Trading212Client
from trading212_mcp.config import Settings
from trading212_mcp.errors import AuthenticationError, MissingCredentialsError, RateLimitError


def build_settings() -> Settings:
    return Settings(
        _env_file=None,
        api_key="key",
        api_secret="secret",
        base_url="https://demo.trading212.com/api/v0",
    )


def test_account_summary_uses_documented_path_and_basic_auth() -> None:
    seen = {}
    expected_auth = "Basic " + base64.b64encode(b"key:secret").decode("ascii")

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["auth"] = request.headers["Authorization"]
        return httpx.Response(200, json={"ok": True})

    async def scenario() -> None:
        transport = httpx.MockTransport(handler)
        async with Trading212Client(build_settings(), transport=transport) as client:
            payload = await client.get_account_summary()
        assert payload == {"ok": True}

    asyncio.run(scenario())

    assert seen == {"path": "/api/v0/equity/account/summary", "auth": expected_auth}


def test_missing_secret_raises_configuration_error() -> None:
    try:
        Trading212Client(
            Settings(
                _env_file=None,
                api_key="key",
                base_url="https://demo.trading212.com/api/v0",
            )
        )
    except MissingCredentialsError as exc:
        assert "T212_API_SECRET" in str(exc)
    else:
        raise AssertionError("Expected MissingCredentialsError")


def test_authentication_errors_are_mapped() -> None:
    async def scenario() -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(401, text=json.dumps({"detail": "bad key"}))
        )
        async with Trading212Client(build_settings(), transport=transport) as client:
            await client.get_account_summary()

    try:
        asyncio.run(scenario())
    except AuthenticationError as exc:
        assert "bad key" in str(exc)
    else:
        raise AssertionError("Expected AuthenticationError")


def test_empty_authentication_error_includes_status_and_endpoint() -> None:
    async def scenario() -> None:
        transport = httpx.MockTransport(lambda request: httpx.Response(401, text="\n"))
        async with Trading212Client(build_settings(), transport=transport) as client:
            await client.get_account_summary()

    try:
        asyncio.run(scenario())
    except AuthenticationError as exc:
        assert str(exc) == (
            "401 Unauthorized from "
            "https://demo.trading212.com/api/v0/equity/account/summary"
        )
    else:
        raise AssertionError("Expected AuthenticationError")


def test_rate_limits_are_mapped() -> None:
    async def scenario() -> None:
        transport = httpx.MockTransport(lambda request: httpx.Response(429, text="slow down"))
        async with Trading212Client(build_settings(), transport=transport) as client:
            await client.list_positions()

    try:
        asyncio.run(scenario())
    except RateLimitError as exc:
        assert "slow down" in str(exc)
    else:
        raise AssertionError("Expected RateLimitError")


def test_historical_orders_use_documented_query_parameters() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = request.url.query.decode()
        return httpx.Response(200, json={"items": [], "nextPagePath": None})

    async def scenario() -> None:
        transport = httpx.MockTransport(handler)
        async with Trading212Client(build_settings(), transport=transport) as client:
            payload = await client.list_historical_orders(cursor=123, ticker="AAPL_US_EQ", limit=21)
        assert payload == {"items": [], "nextPagePath": None}

    asyncio.run(scenario())

    assert seen == {
        "path": "/api/v0/equity/history/orders",
        "query": "cursor=123&ticker=AAPL_US_EQ&limit=21",
    }
