import pytest
from fastapi.testclient import TestClient

from src import config

TEST_DASHBOARD_PASSWORD = "test-password"


def login_client(client: TestClient, password: str = TEST_DASHBOARD_PASSWORD) -> None:
    response = client.post(
        "/login",
        data={"password": password, "next": "/"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"


@pytest.fixture
def app_dirs(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backups"
    config_dir = tmp_path / "config"
    backup_dir.mkdir()
    config_dir.mkdir()

    monkeypatch.setattr(config, "BACKUP_DIR", str(backup_dir))
    monkeypatch.setattr(config, "CONFIG_DIR", str(config_dir))
    monkeypatch.setattr(config, "HISTORY_FILE", str(config_dir / "history.jsonl"))
    monkeypatch.setattr(config, "RETENTION_COUNT", 8)

    return {"backup_dir": backup_dir, "config_dir": config_dir}


@pytest.fixture
def client(app_dirs, monkeypatch):
    monkeypatch.setattr("src.scheduler.start", lambda: None)
    monkeypatch.setattr("src.scheduler.shutdown", lambda: None)
    monkeypatch.setattr("src.config.DASHBOARD_PASSWORD", TEST_DASHBOARD_PASSWORD)

    from src.main import app

    with TestClient(app) as test_client:
        login_client(test_client)
        yield test_client


@pytest.fixture
def unauthenticated_client(app_dirs, monkeypatch):
    monkeypatch.setattr("src.scheduler.start", lambda: None)
    monkeypatch.setattr("src.scheduler.shutdown", lambda: None)
    monkeypatch.setattr("src.config.DASHBOARD_PASSWORD", TEST_DASHBOARD_PASSWORD)

    from src.main import app

    with TestClient(app) as test_client:
        yield test_client
