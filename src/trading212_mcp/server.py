"""Trading 212 MCP server entrypoint."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from threading import Lock
from time import monotonic

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from trading212_mcp.errors import ConfigurationError

from trading212_mcp.client import Trading212Client
from trading212_mcp.config import Settings
from trading212_mcp.tools.account import register_account_tools
from trading212_mcp.tools.history import register_history_tools
from trading212_mcp.tools.metadata import register_metadata_tools
from trading212_mcp.tools.portfolio import register_portfolio_tools

ClientFactory = Callable[[], AsyncIterator[Trading212Client]]


def _matches_protected_path(path: str, protected_path: str) -> bool:
    normalized = protected_path.rstrip("/") or "/"
    return path == normalized or path.startswith(f"{normalized}/")


class BearerTokenAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, protected_path: str, token: str) -> None:
        super().__init__(app)
        self._protected_path = protected_path
        self._token = token

    async def dispatch(self, request: Request, call_next: Callable[..., object]) -> Response:
        if not _matches_protected_path(request.url.path, self._protected_path):
            return await call_next(request)

        authorization = request.headers.get("authorization", "")
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() != "bearer" or credentials != self._token:
            return JSONResponse(
                {"detail": "Missing or invalid bearer token."},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        protected_path: str,
        request_limit: int,
        window_seconds: int,
    ) -> None:
        super().__init__(app)
        self._protected_path = protected_path
        self._request_limit = request_limit
        self._window_seconds = window_seconds
        self._history: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next: Callable[..., object]) -> Response:
        if not _matches_protected_path(request.url.path, self._protected_path):
            return await call_next(request)

        key = self._request_key(request)
        now = monotonic()

        with self._lock:
            timestamps = self._history[key]
            while timestamps and now - timestamps[0] >= self._window_seconds:
                timestamps.popleft()

            if len(timestamps) >= self._request_limit:
                retry_after = max(1, int(self._window_seconds - (now - timestamps[0])))
                return JSONResponse(
                    {
                        "detail": "Rate limit exceeded.",
                        "limit": self._request_limit,
                        "window_seconds": self._window_seconds,
                    },
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )

            timestamps.append(now)

        return await call_next(request)

    @staticmethod
    def _request_key(request: Request) -> str:
        authorization = request.headers.get("authorization", "")
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "bearer" and credentials:
            return f"token:{credentials}"
        client_host = request.client.host if request.client else "anonymous"
        return f"ip:{client_host}"


def create_server(settings: Settings | None = None) -> FastMCP:
    """Create the MCP server with the read-only Trading 212 toolset."""

    app_settings = settings or Settings()
    server = FastMCP(
        name="trading212",
        instructions=(
            "Read-only Trading 212 MCP server backed by the official Public API v0 docs. "
            "Use Basic auth with API key and secret, and prefer demo before live trading."
        ),
        host=app_settings.host,
        port=app_settings.port,
        streamable_http_path=app_settings.streamable_http_path,
    )

    @asynccontextmanager
    async def client_factory() -> AsyncIterator[Trading212Client]:
        async with Trading212Client(app_settings) as client:
            yield client

    @server.custom_route("/health", methods=["GET"], include_in_schema=False)
    async def health_check(_: Request) -> Response:
        return JSONResponse(
            {
                "status": "ok",
                "transport": app_settings.transport,
                "streamable_http_path": app_settings.streamable_http_path,
            }
        )

    register_account_tools(server, client_factory)
    register_portfolio_tools(server, client_factory)
    register_metadata_tools(server, client_factory)
    register_history_tools(server, client_factory)
    return server


def create_http_app(settings: Settings | None = None) -> Starlette:
    app_settings = settings or Settings()
    server = create_server(app_settings)
    app = server.streamable_http_app()

    app.add_middleware(
        RateLimitMiddleware,
        protected_path=app_settings.streamable_http_path,
        request_limit=app_settings.rate_limit_requests,
        window_seconds=app_settings.rate_limit_window_seconds,
    )

    if app_settings.enforce_http_bearer_auth:
        if not app_settings.auth_token:
            raise ConfigurationError(
                "T212_AUTH_TOKEN must be set when T212_ENFORCE_HTTP_BEARER_AUTH is enabled."
            )
        app.add_middleware(
            BearerTokenAuthMiddleware,
            protected_path=app_settings.streamable_http_path,
            token=app_settings.auth_token.get_secret_value(),
        )

    return app


def run_streamable_http(settings: Settings) -> None:
    import uvicorn

    app = create_http_app(settings)
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Trading 212 MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        help="Override the configured FastMCP transport.",
    )
    parser.add_argument("--host", help="Override the HTTP bind host.")
    parser.add_argument("--port", type=int, help="Override the HTTP bind port.")
    parser.add_argument(
        "--streamable-http-path",
        help="Override the Streamable HTTP endpoint path.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the MCP server using the configured transport."""

    args = _parse_args()
    settings = Settings()

    if args.transport:
        settings.transport = args.transport
    if args.host:
        settings.host = args.host
    if args.port is not None:
        settings.port = args.port
    if args.streamable_http_path:
        settings.streamable_http_path = args.streamable_http_path

    if settings.transport == "streamable-http":
        run_streamable_http(settings)
        return

    create_server(settings).run(transport=settings.transport)


if __name__ == "__main__":
    main()
