from trading212_mcp.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.api_key is None
    assert settings.api_secret is None
    assert settings.base_url == "https://demo.trading212.com/api/v0"
    assert settings.timeout_seconds == 10.0
    assert settings.transport == "streamable-http"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.streamable_http_path == "/mcp"
    assert settings.auth_token is None
    assert settings.enforce_http_bearer_auth is True
    assert settings.rate_limit_requests == 30
    assert settings.rate_limit_window_seconds == 60
