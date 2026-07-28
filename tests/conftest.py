import pytest
from fastapi.testclient import TestClient

from app import config

TEST_DASHBOARD_PASSWORD = "test-password"


class AuthenticatedTestClient:
    def __init__(self, client: TestClient):
        self._client = client
        self._auth = ("", TEST_DASHBOARD_PASSWORD)

    def __getattr__(self, name):
        return getattr(self._client, name)

    def request(self, method, url, **kwargs):
        if "auth" not in kwargs:
            kwargs["auth"] = self._auth
        return self._client.request(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)


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
    monkeypatch.setattr("app.scheduler.start", lambda: None)
    monkeypatch.setattr("app.scheduler.shutdown", lambda: None)
    monkeypatch.setattr("app.config.DASHBOARD_PASSWORD", TEST_DASHBOARD_PASSWORD)

    from app.main import app

    with TestClient(app) as test_client:
        yield AuthenticatedTestClient(test_client)
