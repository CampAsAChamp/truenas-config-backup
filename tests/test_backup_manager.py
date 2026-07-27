import time
from unittest.mock import patch

from app import backup_manager, config, history
from app.truenas_client import TrueNASClientError


def _write_backup(app_dirs, name: str, content: bytes = b"tar") -> None:
    path = app_dirs["backup_dir"] / name
    path.write_bytes(content)


def test_list_backups_empty_dir(app_dirs):
    assert backup_manager.list_backups() == []


def test_list_backups_missing_dir(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.setattr(config, "BACKUP_DIR", str(missing))
    assert backup_manager.list_backups() == []


def test_list_backups_ignores_non_tar_and_sorts(app_dirs):
    backup_dir = app_dirs["backup_dir"]
    (backup_dir / "notes.txt").write_text("skip")
    _write_backup(app_dirs, "older.tar")
    time.sleep(0.01)
    _write_backup(app_dirs, "newer.tar")

    backups = backup_manager.list_backups()

    assert len(backups) == 2
    assert backups[0]["filename"] == "newer.tar"
    assert backups[1]["filename"] == "older.tar"
    assert backups[0]["size_bytes"] == 3


def test_backup_path_and_delete(app_dirs):
    _write_backup(app_dirs, "keep.tar")

    assert backup_manager.backup_path("keep.tar") == str(app_dirs["backup_dir"] / "keep.tar")
    assert backup_manager.backup_path("missing.tar") is None

    assert backup_manager.delete_backup("keep.tar") is True
    assert backup_manager.backup_path("keep.tar") is None
    assert backup_manager.delete_backup("keep.tar") is False


def test_delete_backup_blocks_path_traversal(app_dirs):
    _write_backup(app_dirs, "safe.tar")

    assert backup_manager.delete_backup("../config/history.jsonl") is False
    assert (app_dirs["backup_dir"] / "safe.tar").exists()


@patch("app.backup_manager.fetch_config_backup", return_value=b"backup-bytes")
def test_run_backup_success(mock_fetch, app_dirs):
    ok, result = backup_manager.run_backup()

    assert ok is True
    assert result.endswith(".tar")
    mock_fetch.assert_called_once()

    backups = backup_manager.list_backups()
    assert len(backups) == 1
    assert backups[0]["filename"] == result

    entries = history.read_all()
    assert len(entries) == 1
    assert entries[0]["success"] is True
    assert entries[0]["filename"] == result


@patch("app.backup_manager.fetch_config_backup", side_effect=TrueNASClientError("api down"))
def test_run_backup_truenas_error(mock_fetch, app_dirs):
    ok, message = backup_manager.run_backup()

    assert ok is False
    assert message == "api down"
    assert backup_manager.list_backups() == []

    entries = history.read_all()
    assert len(entries) == 1
    assert entries[0]["success"] is False
    assert entries[0]["message"] == "api down"


@patch("app.backup_manager.fetch_config_backup", side_effect=RuntimeError("boom"))
def test_run_backup_unexpected_error(mock_fetch, app_dirs):
    ok, message = backup_manager.run_backup()

    assert ok is False
    assert message == "unexpected error: boom"

    entries = history.read_all()
    assert entries[0]["success"] is False


def test_prune_old_backups(app_dirs, monkeypatch):
    monkeypatch.setattr(config, "RETENTION_COUNT", 2)

    for name in ("one.tar", "two.tar", "three.tar"):
        _write_backup(app_dirs, name)
        time.sleep(0.01)

    with patch("app.backup_manager.fetch_config_backup", return_value=b"x"):
        backup_manager.run_backup()

    names = {b["filename"] for b in backup_manager.list_backups()}
    assert len(names) == 2
    assert "one.tar" not in names
