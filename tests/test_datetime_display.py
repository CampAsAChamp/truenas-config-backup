from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.datetime_display import format_timestamp, to_iso


FIXED_UTC = datetime(2025, 5, 4, 2, 58, 12, tzinfo=timezone.utc)


def test_format_dd_mm_yy_utc():
    result = format_timestamp(
        FIXED_UTC,
        date_format="dd/mm/yy",
        timezone_mode="utc",
    )
    assert result == "04/05/25 02:58"


def test_format_dd_mm_yyyy_manual_timezone():
    result = format_timestamp(
        FIXED_UTC,
        date_format="dd/mm/yyyy",
        timezone_mode="manual",
        timezone_name="America/Los_Angeles",
    )
    assert result == "03/05/2025 19:58:12"


def test_format_mm_dd_yy_utc():
    result = format_timestamp(
        FIXED_UTC,
        date_format="mm/dd/yy",
        timezone_mode="utc",
    )
    assert result == "05/04/25 02:58"


def test_format_mm_dd_yyyy_manual_timezone():
    result = format_timestamp(
        FIXED_UTC,
        date_format="mm/dd/yyyy",
        timezone_mode="manual",
        timezone_name="America/Los_Angeles",
    )
    assert result == "05/03/2025 19:58:12"


def test_format_dd_mm_yy_12h_utc():
    result = format_timestamp(
        FIXED_UTC,
        date_format="dd/mm/yy",
        clock_format="12h",
        timezone_mode="utc",
    )
    assert result == "04/05/25 02:58 AM"


def test_format_mm_dd_yyyy_12h_manual_timezone():
    result = format_timestamp(
        FIXED_UTC,
        date_format="mm/dd/yyyy",
        clock_format="12h",
        timezone_mode="manual",
        timezone_name="America/Los_Angeles",
    )
    assert result == "05/03/2025 07:58:12 PM"


def test_format_iso():
    result = format_timestamp(
        FIXED_UTC,
        date_format="iso",
        timezone_mode="utc",
    )
    assert result == "2025-05-04T02:58:12+00:00"


def test_format_from_iso_string():
    result = format_timestamp(
        "2025-05-04T02:58:12+00:00",
        date_format="dd/mm/yy",
        timezone_mode="utc",
    )
    assert result == "04/05/25 02:58"


def test_invalid_manual_timezone_falls_back_to_utc():
    result = format_timestamp(
        FIXED_UTC,
        date_format="dd/mm/yy",
        timezone_mode="manual",
        timezone_name="Not/A_Real_Zone",
    )
    assert result == "04/05/25 02:58"


def test_format_none_returns_empty():
    assert format_timestamp(None) == ""


def test_to_iso_from_datetime():
    dt = datetime(2025, 5, 4, 2, 58, 12, tzinfo=ZoneInfo("Europe/London"))
    assert to_iso(dt).startswith("2025-05-04T")


def test_to_iso_none_returns_empty():
    assert to_iso(None) == ""
