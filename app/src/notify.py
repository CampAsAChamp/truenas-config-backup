import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone

from . import config

logger = logging.getLogger("truenas_config_backup")

_DISCORD_SUCCESS_COLOR = 5763719
_DISCORD_FAILURE_COLOR = 15548997


def _build_payload(success: bool, message: str, filename: str | None) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()

    if config.NOTIFY_PROVIDER == "discord":
        title = "TrueNAS Config Backup Succeeded" if success else "TrueNAS Config Backup Failed"
        return {
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": _DISCORD_SUCCESS_COLOR if success else _DISCORD_FAILURE_COLOR,
                    "fields": [
                        {"name": "TrueNAS", "value": config.TRUENAS_URL, "inline": True},
                        {"name": "Filename", "value": filename or "—", "inline": True},
                    ],
                    "timestamp": timestamp,
                }
            ],
        }

    return {
        "event": "backup_success" if success else "backup_failure",
        "message": message,
        "timestamp": timestamp,
        "truenas_url": config.TRUENAS_URL,
        "filename": filename,
    }


def notify_backup_result(success: bool, message: str, filename: str | None = None) -> None:
    if not config.NOTIFY_WEBHOOK_URL:
        return
    if success and not config.NOTIFY_ON_SUCCESS:
        return

    payload = _build_payload(success, message, filename)

    try:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            config.NOTIFY_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10):
            pass
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("notification webhook failed: %s", exc)
