import logging
import os
from datetime import datetime, timezone

from . import config, history
from .truenas_client import TrueNASClientError, fetch_config_backup

logger = logging.getLogger("truenas_config_backup")


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


def delete_backup(filename: str) -> bool:
    safe_name = os.path.basename(filename)
    path = os.path.join(config.BACKUP_DIR, safe_name)
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True


def backup_path(filename: str) -> str | None:
    safe_name = os.path.basename(filename)
    path = os.path.join(config.BACKUP_DIR, safe_name)
    return path if os.path.isfile(path) else None


def _prune_old_backups() -> None:
    backups = list_backups()
    for stale in backups[config.RETENTION_COUNT:]:
        try:
            os.remove(os.path.join(config.BACKUP_DIR, stale["filename"]))
        except OSError:
            logger.warning("failed to prune old backup %s", stale["filename"])


def run_backup() -> tuple[bool, str]:
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
        return False, message
    except Exception as exc:  # unexpected transport/auth errors
        message = f"unexpected error: {exc}"
        logger.exception("backup failed unexpectedly")
        history.append(success=False, message=message)
        return False, message

    path = os.path.join(config.BACKUP_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)

    _prune_old_backups()
    history.append(success=True, message="backup completed", filename=filename)
    return True, filename
