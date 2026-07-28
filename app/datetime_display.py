"""Format timestamps for dashboard display (server-side fallback)."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger("truenas_config_backup")

DATE_FORMAT_PRESETS = ("dd/mm/yy", "dd/mm/yyyy", "mm/dd/yy", "mm/dd/yyyy", "iso")
TIMEZONE_MODES = ("local", "utc", "manual")
CLOCK_FORMATS = ("24h", "12h")

_DATE_PARTS = {
    "dd/mm/yy": "%d/%m/%y",
    "dd/mm/yyyy": "%d/%m/%Y",
    "mm/dd/yy": "%m/%d/%y",
    "mm/dd/yyyy": "%m/%d/%Y",
}

_TIME_PARTS = {
    ("24h", False): "%H:%M",
    ("24h", True): "%H:%M:%S",
    ("12h", False): "%I:%M %p",
    ("12h", True): "%I:%M:%S %p",
}


def _parse_timestamp(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _resolve_timezone(mode: str, timezone_name: str) -> timezone | ZoneInfo:
    if mode == "utc":
        return timezone.utc
    if mode == "manual":
        if not timezone_name:
            logger.warning("DISPLAY_TIMEZONE_MODE=manual but DISPLAY_TIMEZONE is empty; using UTC")
            return timezone.utc
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            logger.warning("Invalid DISPLAY_TIMEZONE %r; using UTC", timezone_name)
            return timezone.utc
    tz_name = os.environ.get("TZ")
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            logger.warning("Invalid TZ %r; using UTC", tz_name)
    return timezone.utc


def format_timestamp(
    value: datetime | str | None,
    *,
    date_format: str = "dd/mm/yy",
    clock_format: str = "24h",
    timezone_mode: str = "local",
    timezone_name: str = "",
) -> str:
    if value is None:
        return ""
    dt = _parse_timestamp(value)
    if date_format == "iso":
        return dt.astimezone(timezone.utc).isoformat()
    date_part = _DATE_PARTS.get(date_format, _DATE_PARTS["dd/mm/yy"])
    seconds = date_format.endswith("yyyy")
    clock = clock_format if clock_format in CLOCK_FORMATS else "24h"
    time_part = _TIME_PARTS[(clock, seconds)]
    fmt = f"{date_part} {time_part}"
    tz = _resolve_timezone(timezone_mode, timezone_name)
    return dt.astimezone(tz).strftime(fmt)


def to_iso(value: datetime | str | None) -> str:
    if value is None:
        return ""
    return _parse_timestamp(value).isoformat()
