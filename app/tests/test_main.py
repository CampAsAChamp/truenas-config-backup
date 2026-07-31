from unittest.mock import patch

from conftest import login_client

from src import backup_manager, history
from src.version import get_display_version, get_version


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.text == "OK"


def test_dashboard(client, app_dirs, monkeypatch):
    (app_dirs["backup_dir"] / "sample.tar").write_bytes(b"data")
    monkeypatch.setattr("src.config.TRUENAS_URL", "https://192.168.1.50")
    monkeypatch.setattr("src.config.DISPLAY_DATE_FORMAT", "mm/dd/yy")
    monkeypatch.setattr("src.config.DISPLAY_CLOCK_FORMAT", "12h")
    monkeypatch.setattr("src.config.DISPLAY_TIMEZONE_MODE", "utc")
    monkeypatch.setattr("src.config.DISPLAY_TIMEZONE", "")

    response = client.get("/")

    assert response.status_code == 200
    assert "sample.tar" in response.text
    assert get_display_version() in response.text
    assert "config-field__value--mono" in response.text
    assert "https://192.168.1.50" in response.text
    assert 'id="display-defaults"' in response.text
    assert '"dateFormat": "mm/dd/yy"' in response.text
    assert 'class="timestamp col-timestamp" data-iso=' in response.text
    assert f'href="/static/style.css?v={get_version()}"' in response.text
    assert f'href="/brand/logo.svg?v={get_version()}"' in response.text


def test_download_backup_not_found(client):
    response = client.get("/backups/missing.tar/download")
    assert response.status_code == 404
    assert response.text == "not found"


def test_download_backup_success(client, app_dirs):
    (app_dirs["backup_dir"] / "sample.tar").write_bytes(b"tar-content")

    response = client.get("/backups/sample.tar/download")

    assert response.status_code == 200
    assert response.content == b"tar-content"
    assert response.headers["content-disposition"].endswith('filename="sample.tar"')


def test_delete_backup(client, app_dirs):
    path = app_dirs["backup_dir"] / "remove.tar"
    path.write_bytes(b"x")
    history.append(success=True, message="backup completed", filename="remove.tar")

    response = client.post("/backups/remove.tar/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=backup-deleted&msg=remove.tar"
    assert not path.exists()
    assert history.read_all() == []


def test_delete_backup_missing(client):
    response = client.post("/backups/missing.tar/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=backup-delete-failed&msg=missing.tar"


def test_delete_run_with_backup(client, app_dirs):
    path = app_dirs["backup_dir"] / "remove.tar"
    path.write_bytes(b"x")
    history.append(success=True, message="backup completed", filename="remove.tar")
    timestamp = history.read_all()[0]["timestamp"]

    response = client.post("/runs/delete", data={"timestamp": timestamp}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=run-deleted"
    assert not path.exists()
    assert history.read_all() == []


def test_delete_run_without_backup(client, app_dirs):
    history.append(
        success=True,
        message="backup completed",
        filename="truenas-config-gone.tar",
    )
    timestamp = history.read_all()[0]["timestamp"]

    response = client.post("/runs/delete", data={"timestamp": timestamp}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=run-deleted"
    assert history.read_all() == []


def test_delete_failed_run(client, app_dirs):
    history.append(success=False, message="api down")
    timestamp = history.read_all()[0]["timestamp"]

    response = client.post("/runs/delete", data={"timestamp": timestamp}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=run-deleted"
    assert history.read_all() == []


def test_delete_run_missing(client):
    response = client.post(
        "/runs/delete",
        data={"timestamp": "2026-01-01T00:00:00+00:00"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=run-delete-failed"


def test_dashboard_requires_auth(unauthenticated_client):
    response = unauthenticated_client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2F"


def test_login_rejects_wrong_password(unauthenticated_client):
    response = unauthenticated_client.post(
        "/login",
        data={"password": "wrong-password", "next": "/"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2F&error=1"


def test_login_grants_access(unauthenticated_client):
    login_client(unauthenticated_client)

    response = unauthenticated_client.get("/")

    assert response.status_code == 200


def test_logout_clears_session(client):
    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2F"


def test_healthz_open_without_dashboard_auth(unauthenticated_client):
    response = unauthenticated_client.get("/healthz")

    assert response.status_code == 200
    assert response.text == "OK"


def test_readyz_returns_json(client, app_dirs):
    response = client.get("/readyz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["backup_dir_writable"] is True


@patch("src.main.backup_manager.run_backup", return_value=(True, "truenas-config-20260101-120000.tar"))
def test_run_now(mock_run_backup, client):
    response = client.post("/run-now", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=backup-success&msg=truenas-config-20260101-120000.tar"
    mock_run_backup.assert_called_once()


@patch("src.main.backup_manager.run_backup", return_value=(False, "connection refused"))
def test_run_now_failure(mock_run_backup, client):
    response = client.post("/run-now", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=backup-failure&msg=connection+refused"
    mock_run_backup.assert_called_once()


def test_run_now_executes_backup(client, app_dirs):
    from tar_helpers import make_tar_bytes

    with patch("src.backup_manager.fetch_config_backup", return_value=make_tar_bytes(b"backup")):
        response = client.post("/run-now", follow_redirects=False)

    assert response.status_code == 303
    backups = backup_manager.list_backups()
    assert len(backups) == 1


def test_dashboard_shows_local_version_in_dev_mode(client, app_dirs, monkeypatch):
    monkeypatch.setattr("src.config.DEV_MODE", True)

    response = client.get("/")

    assert response.status_code == 200
    assert get_display_version(dev_mode=True) in response.text
    assert f"v{get_version()}" not in response.text


def test_dashboard_shows_restore_help_link(client, app_dirs):
    response = client.get("/")

    assert response.status_code == 200
    assert "READ-ONLY" in response.text
    assert "Set in the TrueNAS app environment" in response.text
    assert 'href="/help/restore"' in response.text
    assert "How to restore" in response.text
    assert 'href="https://github.com/CampAsAChamp/truenas-config-backup"' in response.text
    assert 'aria-label="View source on GitHub"' in response.text


def test_restore_help_requires_auth(unauthenticated_client):
    response = unauthenticated_client.get("/help/restore", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2Fhelp%2Frestore"


def test_restore_help_page(client):
    response = client.get("/help/restore")

    assert response.status_code == 200
    assert "How to restore a backup" in response.text
    assert "Manage Configuration" in response.text
    assert "Back to dashboard" in response.text
    assert 'href="https://github.com/CampAsAChamp/truenas-config-backup"' in response.text


def test_dashboard_pagination(client, app_dirs, monkeypatch):
    monkeypatch.setattr("src.config.DASHBOARD_PAGE_SIZE", 5)

    for index in range(7):
        history.append(success=False, message=f"failure {index}")

    response = client.get("/")

    assert response.status_code == 200
    assert "Showing 1–5 of 7 runs" in response.text
    assert 'href="/?page=2"' in response.text

    response = client.get("/?page=2")

    assert response.status_code == 200
    assert "Showing 6–7 of 7 runs" in response.text
    assert 'href="/?page=1"' in response.text


def test_dashboard_invalid_page_clamps_to_last_page(client, app_dirs, monkeypatch):
    monkeypatch.setattr("src.config.DASHBOARD_PAGE_SIZE", 5)

    for index in range(7):
        history.append(success=False, message=f"failure {index}")

    response = client.get("/?page=99")

    assert response.status_code == 200
    assert "Showing 6–7 of 7 runs" in response.text


def test_api_logs_requires_auth(unauthenticated_client):
    response = unauthenticated_client.get("/api/logs", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2Fapi%2Flogs"


def test_api_logs_returns_entries(client, app_dirs):
    log_file = app_dirs["config_dir"] / "app.log"
    log_file.write_text(
        "2026-07-29T10:45:00+0000 INFO truenas_config_backup: hello from logs\n",
        encoding="utf-8",
    )

    response = client.get("/api/logs")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["message"] == "hello from logs"


def test_dashboard_includes_logs_panel(client):
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="logs-panel"' in response.text
    assert 'id="logs-list"' in response.text
    assert 'id="logs-clear"' in response.text


def test_api_clear_logs_requires_auth(unauthenticated_client):
    response = unauthenticated_client.post("/api/logs/clear", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=%2Fapi%2Flogs%2Fclear"


def test_api_clear_logs_truncates_file(client, app_dirs):
    log_file = app_dirs["config_dir"] / "app.log"
    log_file.write_text(
        "2026-07-29T10:45:00+0000 INFO truenas_config_backup: stale entry\n",
        encoding="utf-8",
    )

    response = client.post("/api/logs/clear")

    assert response.status_code == 200
    assert response.json() == {"ok": True}

    entries = client.get("/api/logs").json()["entries"]
    assert all(entry["message"] != "stale entry" for entry in entries)


def test_dashboard_includes_editable_config_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="config-settings-form"' in response.text
    assert 'id="config-cron-preset"' in response.text
    assert 'id="config-cron-schedule"' in response.text
    assert 'id="config-cron-schedule-display"' in response.text
    assert 'id="config-next-run-field"' in response.text
    assert 'id="config-unsaved-hint"' in response.text
    assert 'id="config-save-settings"' in response.text


def test_api_settings_updates_persisted(client, app_dirs):
    response = client.post(
        "/api/settings",
        json={
            "cron_schedule": "0 5 * * 1",
            "retention_count": 4,
            "include_secret_seed": True,
            "include_pool_keys": False,
            "include_root_authorized_keys": False,
            "notify_webhook_url": "",
            "notify_on_success": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert "next_run_iso" in payload
    settings_file = app_dirs["config_dir"] / "settings.json"
    assert settings_file.exists()
    assert '"retention_count": 4' in settings_file.read_text()


def test_api_next_run_preview(client):
    response = client.get("/api/settings/next-run",
                          params={"cron_schedule": "0 3 * * 0"})

    assert response.status_code == 200
    assert response.json()["next_run_iso"]


def test_api_next_run_preview_empty_for_manual(client):
    response = client.get("/api/settings/next-run",
                          params={"cron_schedule": ""})

    assert response.status_code == 200
    assert response.json() == {"next_run_iso": ""}


def test_api_next_run_preview_rejects_invalid_cron(client):
    response = client.get("/api/settings/next-run",
                          params={"cron_schedule": "bad"})

    assert response.status_code == 400
