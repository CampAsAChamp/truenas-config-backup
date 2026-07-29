import json
from unittest.mock import patch

from app import config
from app.notify import notify_backup_result


def test_notify_noop_when_url_unset(monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_WEBHOOK_URL", "")

    with patch("app.notify.urllib.request.urlopen") as mock_urlopen:
        notify_backup_result(success=False, message="failed")

    mock_urlopen.assert_not_called()


def test_notify_posts_failure_payload(monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_WEBHOOK_URL", "https://example.com/hook")
    monkeypatch.setattr(config, "NOTIFY_PROVIDER", "generic")
    monkeypatch.setattr(config, "NOTIFY_ON_SUCCESS", False)
    monkeypatch.setattr(config, "TRUENAS_URL", "https://192.168.1.50")

    with patch("app.notify.urllib.request.urlopen") as mock_urlopen:
        notify_backup_result(success=False, message="api down")

    mock_urlopen.assert_called_once()
    request = mock_urlopen.call_args[0][0]
    assert request.full_url == "https://example.com/hook"
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["event"] == "backup_failure"
    assert payload["message"] == "api down"
    assert payload["truenas_url"] == "https://192.168.1.50"


def test_notify_skips_success_by_default(monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_WEBHOOK_URL", "https://example.com/hook")
    monkeypatch.setattr(config, "NOTIFY_ON_SUCCESS", False)

    with patch("app.notify.urllib.request.urlopen") as mock_urlopen:
        notify_backup_result(success=True, message="ok", filename="backup.tar")

    mock_urlopen.assert_not_called()


def test_notify_posts_success_when_enabled(monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_WEBHOOK_URL", "https://example.com/hook")
    monkeypatch.setattr(config, "NOTIFY_ON_SUCCESS", True)
    monkeypatch.setattr(config, "TRUENAS_URL", "https://127.0.0.1")

    with patch("app.notify.urllib.request.urlopen") as mock_urlopen:
        notify_backup_result(success=True, message="ok", filename="backup.tar")

    mock_urlopen.assert_called_once()
    payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
    assert payload["event"] == "backup_success"
    assert payload["filename"] == "backup.tar"


def test_notify_logs_webhook_errors(monkeypatch, caplog):
    monkeypatch.setattr(config, "NOTIFY_WEBHOOK_URL", "https://example.com/hook")

    with patch("app.notify.urllib.request.urlopen", side_effect=OSError("network down")):
        with caplog.at_level("WARNING"):
            notify_backup_result(success=False, message="failed")

    assert "notification webhook failed" in caplog.text


def test_notify_discord_posts_embed_payload(monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_WEBHOOK_URL", "https://discord.com/api/webhooks/test")
    monkeypatch.setattr(config, "NOTIFY_PROVIDER", "discord")
    monkeypatch.setattr(config, "NOTIFY_ON_SUCCESS", False)
    monkeypatch.setattr(config, "TRUENAS_URL", "https://192.168.1.50")

    with patch("app.notify.urllib.request.urlopen") as mock_urlopen:
        notify_backup_result(success=False, message="api down", filename="backup.tar")

    payload = json.loads(mock_urlopen.call_args[0][0].data.decode("utf-8"))
    assert "embeds" in payload
    assert payload["embeds"][0]["title"] == "TrueNAS Config Backup Failed"
    assert payload["embeds"][0]["description"] == "api down"
    assert payload["embeds"][0]["fields"][0]["value"] == "https://192.168.1.50"
    assert payload["embeds"][0]["fields"][1]["value"] == "backup.tar"
