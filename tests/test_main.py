from unittest.mock import patch

from app import backup_manager
from app.version import get_version


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.text == "OK"


def test_dashboard(client, app_dirs, monkeypatch):
    (app_dirs["backup_dir"] / "sample.tar").write_bytes(b"data")
    monkeypatch.setattr("app.config.TRUENAS_URL", "https://192.168.1.50")
    monkeypatch.setattr("app.config.DISPLAY_DATE_FORMAT", "dd/mm/yy")
    monkeypatch.setattr("app.config.DISPLAY_CLOCK_FORMAT", "24h")
    monkeypatch.setattr("app.config.DISPLAY_TIMEZONE_MODE", "utc")
    monkeypatch.setattr("app.config.DISPLAY_TIMEZONE", "")

    response = client.get("/")

    assert response.status_code == 200
    assert "sample.tar" in response.text
    assert f"v{get_version()}" in response.text
    assert '<code class="mono">https://192.168.1.50</code>' in response.text
    assert 'id="display-defaults"' in response.text
    assert '"dateFormat": "dd/mm/yy"' in response.text
    assert 'class="timestamp col-timestamp" data-iso=' in response.text
    assert f'href="/static/style.css?v={get_version()}"' in response.text


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

    response = client.post("/backups/remove.tar/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=backup-deleted&msg=remove.tar"
    assert not path.exists()


def test_delete_backup_missing(client):
    response = client.post("/backups/missing.tar/delete", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=backup-delete-failed&msg=missing.tar"


def test_dashboard_requires_auth_when_password_set(client, monkeypatch):
    monkeypatch.setattr("app.config.DASHBOARD_PASSWORD", "secret")

    response = client.get("/")

    assert response.status_code == 401


def test_dashboard_auth_with_password(client, monkeypatch):
    monkeypatch.setattr("app.config.DASHBOARD_PASSWORD", "secret")

    response = client.get("/", auth=("", "secret"))

    assert response.status_code == 200


def test_healthz_open_when_password_set(client, monkeypatch):
    monkeypatch.setattr("app.config.DASHBOARD_PASSWORD", "secret")

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.text == "OK"


def test_readyz_returns_json(client, app_dirs):
    response = client.get("/readyz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["backup_dir_writable"] is True


@patch("app.main.backup_manager.run_backup", return_value=(True, "truenas-config-20260101-120000.tar"))
def test_run_now(mock_run_backup, client):
    response = client.post("/run-now", follow_redirects=False)

    assert response.status_code == 303
    assert (
        response.headers["location"]
        == "/?toast=backup-success&msg=truenas-config-20260101-120000.tar"
    )
    mock_run_backup.assert_called_once()


@patch("app.main.backup_manager.run_backup", return_value=(False, "connection refused"))
def test_run_now_failure(mock_run_backup, client):
    response = client.post("/run-now", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/?toast=backup-failure&msg=connection+refused"
    mock_run_backup.assert_called_once()


def test_run_now_executes_backup(client, app_dirs):
    from tests.tar_helpers import make_tar_bytes

    with patch("app.backup_manager.fetch_config_backup", return_value=make_tar_bytes(b"backup")):
        response = client.post("/run-now", follow_redirects=False)

    assert response.status_code == 303
    backups = backup_manager.list_backups()
    assert len(backups) == 1
