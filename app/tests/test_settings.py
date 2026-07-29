import pytest

from src import config
from src.config_validation import validate_loaded_settings
from src.settings import load_settings_from_env, resolve_notify_provider, validate_settings


def test_load_settings_defaults():
    s = load_settings_from_env({})
    assert s.truenas.url == "https://127.0.0.1"
    assert s.truenas.api_key == ""
    assert s.backup.retention_count == 8
    assert s.display.date_format == "mm/dd/yy"


def test_load_settings_from_env():
    s = load_settings_from_env(
        {
            "TRUENAS_URL": "https://192.168.1.50/",
            "TRUENAS_API_KEY": "secret-key",
            "RETENTION_COUNT": "12",
            "DASHBOARD_PASSWORD": "pw",
            "NOTIFY_WEBHOOK_URL": "https://example.com/hook",
        }
    )
    assert s.truenas.url == "https://192.168.1.50"
    assert s.backup.retention_count == 12
    assert s.notify.webhook_url == "https://example.com/hook"


def test_reload_settings_updates_module_aliases(monkeypatch):
    monkeypatch.setenv("TRUENAS_URL", "https://nas.local")
    monkeypatch.setenv("RETENTION_COUNT", "5")
    config.reload_settings()
    assert config.TRUENAS_URL == "https://nas.local"
    assert config.RETENTION_COUNT == 5


def test_validate_settings_rejects_missing_password():
    s = load_settings_from_env({})
    with pytest.raises(ValueError, match="DASHBOARD_PASSWORD"):
        validate_settings(s)


def test_validate_settings_rejects_invalid_cron():
    s = load_settings_from_env({"DASHBOARD_PASSWORD": "pw", "CRON_SCHEDULE": "bad"})
    with pytest.raises(ValueError):
        validate_settings(s)


def test_validate_settings_rejects_negative_retention():
    s = load_settings_from_env({"DASHBOARD_PASSWORD": "pw", "RETENTION_COUNT": "-1"})
    with pytest.raises(ValueError, match="RETENTION_COUNT"):
        validate_settings(s)


def test_validate_settings_rejects_invalid_notify_provider():
    s = load_settings_from_env({"DASHBOARD_PASSWORD": "pw", "NOTIFY_PROVIDER": "slack"})
    with pytest.raises(ValueError, match="NOTIFY_PROVIDER"):
        validate_settings(s)


def test_validate_loaded_settings_accepts_valid_env(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    config.reload_settings()
    validate_loaded_settings()


@pytest.mark.parametrize(
    ("url", "explicit", "expected"),
    [
        ("", "generic", "generic"),
        ("https://discord.com/api/webhooks/1/2", "generic", "discord"),
        ("https://hooks.slack.com/x", "generic", "generic"),
        ("https://hooks.slack.com/x", "discord", "discord"),
    ],
)
def test_resolve_notify_provider(url, explicit, expected):
    assert resolve_notify_provider(url, explicit) == expected


def test_notify_effective_provider_auto_detects_discord():
    s = load_settings_from_env(
        {
            "DASHBOARD_PASSWORD": "pw",
            "NOTIFY_WEBHOOK_URL": "https://discord.com/api/webhooks/123/abc",
        }
    )
    assert s.notify.effective_provider == "discord"
