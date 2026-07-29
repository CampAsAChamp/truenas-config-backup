import time
import threading
from unittest.mock import patch

from app import backup_manager, config, history
from app.truenas_client import TrueNASClientError
from tar_helpers import make_tar_bytes


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


@patch("app.backup_manager.fetch_config_backup", return_value=make_tar_bytes())
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


def test_delete_backup_removes_history(app_dirs):
    _write_backup(app_dirs, "keep.tar")
    history.append(success=True, message="backup completed", filename="keep.tar")

    assert backup_manager.delete_backup("keep.tar") is True

    assert backup_manager.list_backups() == []
    assert history.read_all() == []


def test_delete_run_removes_backup_and_history(app_dirs):
    _write_backup(app_dirs, "keep.tar")
    history.append(success=True, message="backup completed", filename="keep.tar")
    timestamp = history.read_all()[0]["timestamp"]

    assert backup_manager.delete_run(timestamp) is True

    assert backup_manager.list_backups() == []
    assert history.read_all() == []


def test_delete_run_removes_history_when_backup_gone(app_dirs):
    history.append(
        success=True,
        message="backup completed",
        filename="truenas-config-gone.tar",
    )
    timestamp = history.read_all()[0]["timestamp"]

    assert backup_manager.delete_run(timestamp) is True
    assert history.read_all() == []


def test_delete_run_removes_failed_history(app_dirs):
    history.append(success=False, message="api down")
    timestamp = history.read_all()[0]["timestamp"]

    assert backup_manager.delete_run(timestamp) is True
    assert history.read_all() == []


def test_delete_run_orphan_backup_without_history(app_dirs):
    _write_backup(app_dirs, "orphan.tar")
    runs = backup_manager.list_backup_runs()
    timestamp = runs[0]["timestamp"]

    assert backup_manager.delete_run(timestamp) is True
    assert backup_manager.list_backups() == []


def test_delete_run_unknown_timestamp(app_dirs):
    assert backup_manager.delete_run("2026-01-01T00:00:00+00:00") is False


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

    with patch("app.backup_manager.fetch_config_backup", return_value=make_tar_bytes(b"x")):
        backup_manager.run_backup()

    names = {b["filename"] for b in backup_manager.list_backups()}
    assert len(names) == 2
    assert "one.tar" not in names


def test_list_backup_runs_joins_history(app_dirs):
    _write_backup(app_dirs, "truenas-config-20260101-120000.tar")
    history.append(
        success=True,
        message="backup completed",
        filename="truenas-config-20260101-120000.tar",
    )
    history.append(success=False, message="api down")

    runs = backup_manager.list_backup_runs()
    success_entry = next(e for e in history.read_all() if e.get("filename"))
    failure_entry = next(e for e in history.read_all() if not e.get("success"))

    assert len(runs) == 2
    assert runs[0]["success"] is False
    assert runs[0]["has_backup"] is False
    assert runs[0]["filename"] is None
    assert runs[0]["message"] == "api down"
    assert runs[0]["timestamp"] == failure_entry["timestamp"]

    assert runs[1]["success"] is True
    assert runs[1]["has_backup"] is True
    assert runs[1]["filename"] == "truenas-config-20260101-120000.tar"
    assert runs[1]["message"] == "backup completed"
    assert runs[1]["timestamp"] == success_entry["timestamp"]


def test_list_backup_runs_without_history_uses_file_mtime(app_dirs):
    _write_backup(app_dirs, "orphan.tar")

    runs = backup_manager.list_backup_runs()

    assert len(runs) == 1
    assert runs[0]["success"] is True
    assert runs[0]["has_backup"] is True
    assert runs[0]["filename"] == "orphan.tar"
    assert runs[0]["message"] == ""
    assert runs[0]["timestamp"] == backup_manager.list_backups()[0]["modified"]


def test_list_backup_runs_page_returns_slice_and_total(app_dirs):
    for index in range(25):
        history.append(
            success=False,
            message=f"failure {index}",
        )

    page_runs, total = backup_manager.list_backup_runs_page(offset=0, limit=20)

    assert total == 25
    assert len(page_runs) == 20

    page_runs, total = backup_manager.list_backup_runs_page(offset=20, limit=20)

    assert total == 25
    assert len(page_runs) == 5


@patch("app.backup_manager.fetch_config_backup", return_value=b"not-a-tar")
def test_run_backup_rejects_invalid_tar(mock_fetch, app_dirs):
    ok, message = backup_manager.run_backup()

    assert ok is False
    assert message == "invalid backup file"
    assert backup_manager.list_backups() == []


@patch("app.backup_manager.fetch_config_backup", return_value=make_tar_bytes())
def test_run_backup_blocks_concurrent_runs(mock_fetch, app_dirs):
    started = threading.Event()
    release = threading.Event()

    def slow_fetch(*args, **kwargs):
        started.set()
        release.wait(timeout=2)
        return make_tar_bytes()

    mock_fetch.side_effect = slow_fetch

    results: list[tuple[bool, str]] = []

    def first_run():
        results.append(backup_manager.run_backup())

    thread = threading.Thread(target=first_run)
    thread.start()
    assert started.wait(timeout=2)

    results.append(backup_manager.run_backup())
    release.set()
    thread.join(timeout=2)

    assert results[0] == (False, "backup already in progress")
    assert results[1][0] is True


@patch("app.backup_manager._execute_backup", return_value=(True, "backup.tar"))
def test_run_scheduled_backup_skips_when_busy(mock_execute, app_dirs):
    backup_manager._backup_lock.acquire()
    try:
        backup_manager.run_scheduled_backup()
    finally:
        backup_manager._backup_lock.release()

    mock_execute.assert_not_called()
    entries = history.read_all()
    assert entries[0]["message"] == "skipped: backup already in progress"
