"""Typed models shared across the MCP server."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HistoryPageParams(BaseModel):
    """Cursor-based pagination inputs used by Trading 212 history endpoints."""

    limit: int = Field(default=20, ge=1, le=50)


class UpstreamPayload(BaseModel):
    """Standard wrapper used by MCP tools for upstream data."""

    source: str = Field(default="trading212")
    data: dict[str, Any] | list[dict[str, Any]] | list[Any] | str | int | float | bool | None
