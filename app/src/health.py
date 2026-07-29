import os
from datetime import datetime, timezone

from . import config, history
from .truenas_client import TrueNASClientError, check_truenas_connection


def _dir_writable(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_probe")
        with open(probe, "w") as handle:
            handle.write("ok")
        os.remove(probe)
        return True
    except OSError:
        return False


def _last_backup_summary() -> dict | None:
    for entry in history.read_all():
        timestamp = entry.get("timestamp")
        if not timestamp:
            continue
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            age_seconds = int((datetime.now(timezone.utc) - parsed).total_seconds())
        except ValueError:
            age_seconds = None
        return {
            "success": entry.get("success", False),
            "timestamp": timestamp,
            "age_seconds": age_seconds,
            "message": entry.get("message", ""),
        }
    return None


def readiness_status() -> dict:
    backup_dir_writable = _dir_writable(config.BACKUP_DIR)
    config_dir_writable = _dir_writable(config.CONFIG_DIR)
    last_backup = _last_backup_summary()

    ready = backup_dir_writable and config_dir_writable
    if last_backup is not None and not last_backup["success"]:
        ready = False

    truenas_reachable = None
    if config.HEALTH_CHECK_TRUENAS:
        try:
            check_truenas_connection(
                base_url=config.TRUENAS_URL,
                api_key=config.TRUENAS_API_KEY,
                verify_ssl=config.TRUENAS_VERIFY_SSL,
            )
            truenas_reachable = True
        except (TrueNASClientError, OSError):
            truenas_reachable = False
            ready = False

    return {
        "ready": ready,
        "backup_dir_writable": backup_dir_writable,
        "config_dir_writable": config_dir_writable,
        "last_backup": last_backup,
        "truenas_reachable": truenas_reachable,
    }
