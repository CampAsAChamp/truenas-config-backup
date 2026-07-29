import json

from src.settings import load_settings_from_env
from src.settings_store import load_persisted, load_settings, save_persisted, update_persisted
from src.settings_store import PersistedSettings, seed_if_missing


def test_seed_and_load_persisted(tmp_path):
    config_dir = str(tmp_path / "config")
    base = load_settings_from_env({"CONFIG_DIR": config_dir, "DASHBOARD_PASSWORD": "pw"})
    seed_if_missing(config_dir, base)
    path = tmp_path / "config" / "settings.json"
    assert path.exists()
    persisted = load_persisted(config_dir)
    assert persisted is not None
    assert persisted.retention_count == 8


def test_persisted_overrides_env_tunable_fields(tmp_path, monkeypatch):
    config_dir = str(tmp_path / "config")
    monkeypatch.setenv("CONFIG_DIR", config_dir)
    monkeypatch.setenv("DASHBOARD_PASSWORD", "pw")
    monkeypatch.setenv("RETENTION_COUNT", "8")
    save_persisted(config_dir, PersistedSettings(retention_count=3, cron_schedule="0 4 * * *"))
    s = load_settings()
    assert s.backup.retention_count == 3
    assert s.backup.cron_schedule == "0 4 * * *"


def test_update_persisted_merges(tmp_path):
    config_dir = str(tmp_path / "config")
    update_persisted(config_dir, {"retention_count": 5})
    update_persisted(config_dir, {"cron_schedule": "0 1 * * *"})
    data = json.loads((tmp_path / "config" / "settings.json").read_text())
    assert data["retention_count"] == 5
    assert data["cron_schedule"] == "0 1 * * *"
