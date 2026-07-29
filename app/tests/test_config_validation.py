import pytest
from apscheduler.triggers.cron import CronTrigger

from src import config
from src.config_validation import validate_config


def test_validate_config_rejects_missing_dashboard_password(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "")
    monkeypatch.setattr(config, "TRUENAS_API_KEY", "key")
    monkeypatch.setattr(config, "CRON_SCHEDULE", "")
    monkeypatch.setattr(config, "RETENTION_COUNT", 8)

    with pytest.raises(ValueError, match="DASHBOARD_PASSWORD"):
        validate_config()


def test_validate_config_warns_on_missing_api_key(monkeypatch, caplog):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret")
    monkeypatch.setattr(config, "TRUENAS_API_KEY", "")
    monkeypatch.setattr(config, "CRON_SCHEDULE", "")
    monkeypatch.setattr(config, "RETENTION_COUNT", 8)

    with caplog.at_level("WARNING"):
        validate_config()

    assert "TRUENAS_API_KEY is not set" in caplog.text


def test_validate_config_rejects_invalid_cron(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret")
    monkeypatch.setattr(config, "TRUENAS_API_KEY", "key")
    monkeypatch.setattr(config, "CRON_SCHEDULE", "not-a-cron")
    monkeypatch.setattr(config, "RETENTION_COUNT", 8)

    with pytest.raises(ValueError):
        validate_config()


def test_validate_config_rejects_negative_retention(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret")
    monkeypatch.setattr(config, "TRUENAS_API_KEY", "key")
    monkeypatch.setattr(config, "CRON_SCHEDULE", "")
    monkeypatch.setattr(config, "RETENTION_COUNT", -1)

    with pytest.raises(ValueError, match="RETENTION_COUNT"):
        validate_config()


def test_validate_config_accepts_valid_cron(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret")
    monkeypatch.setattr(config, "TRUENAS_API_KEY", "key")
    monkeypatch.setattr(config, "CRON_SCHEDULE", "0 3 * * 0")
    monkeypatch.setattr(config, "RETENTION_COUNT", 8)
    monkeypatch.setattr(config, "DASHBOARD_PAGE_SIZE", 20)
    monkeypatch.setattr(config, "NOTIFY_PROVIDER", "generic")

    validate_config()
    CronTrigger.from_crontab(config.CRON_SCHEDULE)


def test_validate_config_rejects_invalid_page_size(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret")
    monkeypatch.setattr(config, "TRUENAS_API_KEY", "key")
    monkeypatch.setattr(config, "CRON_SCHEDULE", "")
    monkeypatch.setattr(config, "RETENTION_COUNT", 8)
    monkeypatch.setattr(config, "DASHBOARD_PAGE_SIZE", 0)
    monkeypatch.setattr(config, "NOTIFY_PROVIDER", "generic")

    with pytest.raises(ValueError, match="DASHBOARD_PAGE_SIZE"):
        validate_config()


def test_validate_config_rejects_invalid_notify_provider(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_PASSWORD", "secret")
    monkeypatch.setattr(config, "TRUENAS_API_KEY", "key")
    monkeypatch.setattr(config, "CRON_SCHEDULE", "")
    monkeypatch.setattr(config, "RETENTION_COUNT", 8)
    monkeypatch.setattr(config, "DASHBOARD_PAGE_SIZE", 20)
    notify = config.settings.notify.model_copy(update={"provider": "slack"})
    monkeypatch.setattr(
        config,
        "settings",
        config.settings.model_copy(update={"notify": notify}),
    )

    with pytest.raises(ValueError, match="NOTIFY_PROVIDER"):
        validate_config()
