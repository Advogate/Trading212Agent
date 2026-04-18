"""HTTP client for Trading 212 API access."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from trading212_mcp.config import Settings
from trading212_mcp.errors import (
    AuthenticationError,
    MissingCredentialsError,
    RateLimitError,
    UpstreamAPIError,
)


class Trading212Client:
    """Thin async client around the Trading 212 HTTP API."""

    ACCOUNT_SUMMARY_PATH = "/equity/account/summary"
    POSITIONS_PATH = "/equity/positions"
    EXCHANGES_PATH = "/equity/metadata/exchanges"
    INSTRUMENTS_PATH = "/equity/metadata/instruments"
    HISTORY_DIVIDENDS_PATH = "/equity/history/dividends"
    HISTORY_EXPORTS_PATH = "/equity/history/exports"
    HISTORY_ORDERS_PATH = "/equity/history/orders"
    HISTORY_TRANSACTIONS_PATH = "/equity/history/transactions"

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not settings.base_url or not settings.api_key or not settings.api_secret:
            raise MissingCredentialsError(
                "Missing Trading 212 configuration. Set T212_BASE_URL, T212_API_KEY, and "
                "T212_API_SECRET before calling upstream tools."
            )

        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            headers={
                "Authorization": self._build_auth_header_value(settings),
                "Accept": "application/json",
                "User-Agent": settings.user_agent,
            },
            transport=transport,
        )

    async def __aenter__(self) -> Trading212Client:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def get_account_summary(self) -> Any:
        return await self._get_json(self.ACCOUNT_SUMMARY_PATH)

    async def list_positions(self, ticker: str | None = None) -> Any:
        return await self._get_json(self.POSITIONS_PATH, params={"ticker": ticker})

    async def list_exchanges(self) -> Any:
        return await self._get_json(self.EXCHANGES_PATH)

    async def list_instruments(self) -> Any:
        return await self._get_json(self.INSTRUMENTS_PATH)

    async def list_dividends(
        self,
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int = 20,
    ) -> Any:
        return await self._get_json(
            self.HISTORY_DIVIDENDS_PATH,
            params={"cursor": cursor, "ticker": ticker, "limit": limit},
        )

    async def list_export_reports(self) -> Any:
        return await self._get_json(self.HISTORY_EXPORTS_PATH)

    async def list_historical_orders(
        self,
        cursor: int | None = None,
        ticker: str | None = None,
        limit: int = 20,
    ) -> Any:
        return await self._get_json(
            self.HISTORY_ORDERS_PATH,
            params={"cursor": cursor, "ticker": ticker, "limit": limit},
        )

    async def list_transactions(
        self,
        cursor: str | None = None,
        time: str | None = None,
        limit: int = 20,
    ) -> Any:
        return await self._get_json(
            self.HISTORY_TRANSACTIONS_PATH,
            params={"cursor": cursor, "time": time, "limit": limit},
        )

    @staticmethod
    def _build_auth_header_value(settings: Settings) -> str:
        api_key = settings.api_key.get_secret_value() if settings.api_key else ""
        api_secret = settings.api_secret.get_secret_value() if settings.api_secret else ""
        encoded = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode("ascii")
        return f"Basic {encoded}"

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        filtered_params = {k: v for k, v in (params or {}).items() if v is not None}
        response = await self._client.get(path, params=filtered_params)
        self._raise_for_status(response)
        return response.json()

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return

        message = response.text.strip() or (
            f"{response.status_code} {response.reason_phrase} from {response.request.url}"
        )
        if response.status_code in {401, 403}:
            raise AuthenticationError(message)
        if response.status_code == 429:
            raise RateLimitError(message)
        raise UpstreamAPIError(response.status_code, message)
