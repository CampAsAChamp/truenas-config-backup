"""Format byte counts for dashboard display."""

from __future__ import annotations

_UNITS = ("B", "KB", "MB", "GB", "TB")


def format_bytes(size_bytes: int | None) -> str:
    if size_bytes is None:
        return ""

    size = float(max(size_bytes, 0))
    unit_idx = 0
    while size >= 1024 and unit_idx < len(_UNITS) - 1:
        size /= 1024
        unit_idx += 1

    if unit_idx == 0:
        return f"{int(size)} {_UNITS[unit_idx]}"

    if size >= 100:
        formatted = f"{size:.0f}"
    elif size >= 10:
        formatted = f"{size:.1f}".rstrip("0").rstrip(".")
    else:
        formatted = f"{size:.2f}".rstrip("0").rstrip(".")

    return f"{formatted} {_UNITS[unit_idx]}"
