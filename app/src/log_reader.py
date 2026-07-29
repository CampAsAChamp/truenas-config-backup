"""Read and parse tail lines from the application log file."""

from __future__ import annotations

import os
import re

from . import config

LOG_LINE_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{4}) "
    r"(?P<level>\w+) truenas_config_backup: (?P<message>.*)$"
)


def _normalize_timestamp(timestamp: str) -> str:
    if timestamp.endswith("+0000"):
        return timestamp[:-5] + "Z"
    return timestamp


def tail_log_entries(limit: int | None = None) -> list[dict]:
    """Return the last N parsed log entries from the log file."""
    max_lines = limit if limit is not None else config.LOG_TAIL_LIMIT
    max_lines = max(1, min(max_lines, config.LOG_TAIL_LIMIT))

    path = config.LOG_FILE
    if not os.path.isfile(path):
        return []

    with open(path, encoding="utf-8") as handle:
        lines = handle.readlines()

    entries: list[dict] = []
    for line in lines[-max_lines:]:
        text = line.rstrip("\n")
        if not text:
            continue
        match = LOG_LINE_RE.match(text)
        if match:
            entries.append({
                "timestamp": _normalize_timestamp(match.group("timestamp")),
                "level": match.group("level"),
                "message": match.group("message"),
            })
        else:
            entries.append({
                "timestamp": "",
                "level": "INFO",
                "message": text,
            })
    return entries
