from unittest.mock import patch

from app import backup_manager


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.text == "OK"


def test_dashboard(client, app_dirs):
    (app_dirs["backup_dir"] / "sample.tar").write_bytes(b"data")

    response = client.get("/")

    assert response.status_code == 200
    assert "sample.tar" in response.text


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
    assert response.headers["location"] == "/"
    assert not path.exists()


@patch("app.main.backup_manager.run_backup", return_value=(True, "truenas-config-20260101-120000.tar"))
def test_run_now(mock_run_backup, client):
    response = client.post("/run-now", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    mock_run_backup.assert_called_once()


def test_run_now_executes_backup(client, app_dirs):
    with patch("app.backup_manager.fetch_config_backup", return_value=b"backup"):
        response = client.post("/run-now", follow_redirects=False)

    assert response.status_code == 303
    backups = backup_manager.list_backups()
    assert len(backups) == 1
