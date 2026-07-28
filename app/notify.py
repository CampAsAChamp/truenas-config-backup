import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timezone

from . import config

logger = logging.getLogger("truenas_config_backup")


def notify_backup_result(success: bool, message: str, filename: str | None = None) -> None:
    if not config.NOTIFY_WEBHOOK_URL:
        return
    if success and not config.NOTIFY_ON_SUCCESS:
        return

    payload = {
        "event": "backup_success" if success else "backup_failure",
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "truenas_url": config.TRUENAS_URL,
        "filename": filename,
    }

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
