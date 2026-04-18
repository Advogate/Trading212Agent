"""Error types for Trading 212 integration."""

from __future__ import annotations


class Trading212Error(Exception):
    """Base exception for Trading 212 integration failures."""


class ConfigurationError(Trading212Error):
    """Raised when required local configuration is missing or invalid."""


class MissingCredentialsError(ConfigurationError):
    """Raised when the API key, secret, or base URL is missing."""


class AuthenticationError(Trading212Error):
    """Raised when the upstream API rejects credentials."""


class RateLimitError(Trading212Error):
    """Raised when the upstream API rate limits a request."""


class UpstreamAPIError(Trading212Error):
    """Raised when the Trading 212 API returns an unexpected error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Trading 212 API request failed with status {status_code}: {message}")
