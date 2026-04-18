from trading212_mcp.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings()

    assert settings.api_key is None
    assert settings.api_secret is None
    assert settings.base_url == "https://demo.trading212.com/api/v0"
    assert settings.timeout_seconds == 10.0
