import json
import os
from datetime import datetime, timezone

from . import config


def _ensure_parent() -> None:
    os.makedirs(os.path.dirname(config.HISTORY_FILE), exist_ok=True)


def append(success: bool, message: str, filename: str | None = None) -> None:
    _ensure_parent()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "message": message,
        "filename": filename,
    }
    with open(config.HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_all() -> list[dict]:
    if not os.path.exists(config.HISTORY_FILE):
        return []
    entries = []
    with open(config.HISTORY_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    entries.reverse()
    return entries
