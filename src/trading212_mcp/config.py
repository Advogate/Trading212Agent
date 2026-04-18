"""Configuration for the Trading 212 MCP server."""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration for the MCP server and upstream API."""

    model_config = SettingsConfigDict(
        env_prefix="T212_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr | None = Field(default=None)
    api_secret: SecretStr | None = Field(default=None)
    base_url: str = Field(default="https://demo.trading212.com/api/v0")
    timeout_seconds: float = Field(default=10.0, gt=0)
    user_agent: str = Field(default="trading212-mcp/0.1.0")
