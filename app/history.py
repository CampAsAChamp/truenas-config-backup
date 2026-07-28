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


def _rewrite_entries(keep: list[str]) -> None:
    _ensure_parent()
    with open(config.HISTORY_FILE, "w") as f:
        for line in keep:
            f.write(line)


def delete_by_timestamp(timestamp: str) -> bool:
    if not os.path.exists(config.HISTORY_FILE):
        return False
    kept: list[str] = []
    removed = False
    with open(config.HISTORY_FILE) as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError:
                kept.append(line if line.endswith("\n") else line + "\n")
                continue
            if entry.get("timestamp") == timestamp:
                removed = True
                continue
            kept.append(line if line.endswith("\n") else line + "\n")
    if removed:
        _rewrite_entries(kept)
    return removed


def delete_by_filename(filename: str) -> bool:
    safe_name = os.path.basename(filename)
    if not os.path.exists(config.HISTORY_FILE):
        return False
    kept: list[str] = []
    removed = False
    with open(config.HISTORY_FILE) as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError:
                kept.append(line if line.endswith("\n") else line + "\n")
                continue
            if entry.get("filename") == safe_name:
                removed = True
                continue
            kept.append(line if line.endswith("\n") else line + "\n")
    if removed:
        _rewrite_entries(kept)
    return removed
