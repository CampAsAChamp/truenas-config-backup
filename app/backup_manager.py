import logging
import os
import tarfile
import threading
from datetime import datetime, timezone

from . import config, history
from .notify import notify_backup_result
from .truenas_client import TrueNASClientError, fetch_config_backup

logger = logging.getLogger("truenas_config_backup")

_backup_lock = threading.Lock()


def _filename() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"truenas-config-{stamp}.tar"


def list_backups() -> list[dict]:
    if not os.path.isdir(config.BACKUP_DIR):
        return []
    backups = []
    for name in os.listdir(config.BACKUP_DIR):
        if not name.endswith(".tar"):
            continue
        path = os.path.join(config.BACKUP_DIR, name)
        stat = os.stat(path)
        backups.append({
            "filename": name,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })
    backups.sort(key=lambda b: b["modified"], reverse=True)
    return backups


def list_backup_runs(limit: int | None = 20) -> list[dict]:
    """Run history merged with on-disk backups (newest first)."""
    backups_by_name = {b["filename"]: b for b in list_backups()}
    claimed: set[str] = set()
    runs: list[dict] = []

    for entry in history.read_all():
        success = entry.get("success", False)
        filename = entry.get("filename")
        if success and filename and filename in backups_by_name:
            backup = backups_by_name[filename]
            claimed.add(filename)
            runs.append({
                "success": True,
                "has_backup": True,
                "timestamp": entry["timestamp"],
                "filename": filename,
                "size_bytes": backup["size_bytes"],
                "message": entry.get("message", ""),
            })
        elif success and filename:
            runs.append({
                "success": True,
                "has_backup": False,
                "timestamp": entry["timestamp"],
                "filename": filename,
                "size_bytes": None,
                "message": entry.get("message", ""),
            })
        elif not success:
            runs.append({
                "success": False,
                "has_backup": False,
                "timestamp": entry["timestamp"],
                "filename": None,
                "size_bytes": None,
                "message": entry.get("message", ""),
            })

    for backup in list_backups():
        if backup["filename"] not in claimed:
            runs.append({
                "success": True,
                "has_backup": True,
                "timestamp": backup["modified"],
                "filename": backup["filename"],
                "size_bytes": backup["size_bytes"],
                "message": "",
            })

    runs.sort(key=lambda run: run["timestamp"], reverse=True)
    if limit is not None:
        runs = runs[:limit]
    return runs


def delete_backup(filename: str) -> bool:
    safe_name = os.path.basename(filename)
    path = os.path.join(config.BACKUP_DIR, safe_name)
    if not os.path.isfile(path):
        return False
    os.remove(path)
    history.delete_by_filename(safe_name)
    return True


def delete_run(timestamp: str) -> bool:
    """Remove a run from history and delete its backup file when still on disk."""
    runs = list_backup_runs(limit=None)
    run = next((item for item in runs if item["timestamp"] == timestamp), None)
    if not run:
        return False

    deleted = False
    if run.get("has_backup") and run.get("filename"):
        if delete_backup(run["filename"]):
            deleted = True

    if history.delete_by_timestamp(timestamp):
        deleted = True

    return deleted


def backup_path(filename: str) -> str | None:
    safe_name = os.path.basename(filename)
    path = os.path.join(config.BACKUP_DIR, safe_name)
    return path if os.path.isfile(path) else None


def _prune_old_backups() -> None:
    if config.RETENTION_COUNT <= 0:
        return
    backups = list_backups()
    for stale in backups[config.RETENTION_COUNT:]:
        try:
            os.remove(os.path.join(config.BACKUP_DIR, stale["filename"]))
        except OSError:
            logger.warning("failed to prune old backup %s", stale["filename"])


def _execute_backup() -> tuple[bool, str]:
    os.makedirs(config.BACKUP_DIR, exist_ok=True)
    filename = _filename()
    try:
        content = fetch_config_backup(
            base_url=config.TRUENAS_URL,
            api_key=config.TRUENAS_API_KEY,
            verify_ssl=config.TRUENAS_VERIFY_SSL,
            include_secret_seed=config.INCLUDE_SECRET_SEED,
        )
    except TrueNASClientError as exc:
        message = str(exc)
        logger.error("backup failed: %s", message)
        history.append(success=False, message=message)
        notify_backup_result(success=False, message=message)
        return False, message
    except Exception as exc:
        message = f"unexpected error: {exc}"
        logger.exception("backup failed unexpectedly")
        history.append(success=False, message=message)
        notify_backup_result(success=False, message=message)
        return False, message

    path = os.path.join(config.BACKUP_DIR, filename)
    with open(path, "wb") as handle:
        handle.write(content)

    if not tarfile.is_tarfile(path):
        try:
            os.remove(path)
        except OSError:
            logger.warning("failed to remove invalid backup file %s", filename)
        message = "invalid backup file"
        logger.error("backup failed: %s", message)
        history.append(success=False, message=message)
        notify_backup_result(success=False, message=message)
        return False, message

    _prune_old_backups()
    history.append(success=True, message="backup completed", filename=filename)
    notify_backup_result(success=True, message="backup completed", filename=filename)
    return True, filename


def run_backup() -> tuple[bool, str]:
    if not _backup_lock.acquire(blocking=False):
        return False, "backup already in progress"
    try:
        return _execute_backup()
    finally:
        _backup_lock.release()


def run_scheduled_backup() -> None:
    if not _backup_lock.acquire(blocking=False):
        logger.warning("scheduled backup skipped: already in progress")
        history.append(success=False, message="skipped: backup already in progress")
        return
    try:
        _execute_backup()
    finally:
        _backup_lock.release()
