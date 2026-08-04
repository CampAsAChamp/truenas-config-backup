from src.format_bytes import format_bytes


def test_format_bytes_none_returns_empty():
    assert format_bytes(None) == ""


def test_format_bytes_shows_bytes():
    assert format_bytes(500) == "500 B"
    assert format_bytes(3) == "3 B"


def test_format_bytes_shows_kilobytes():
    assert format_bytes(811 * 1024) == "811 KB"
    assert format_bytes(1024) == "1 KB"
    assert format_bytes(1536) == "1.5 KB"


def test_format_bytes_shows_megabytes():
    assert format_bytes(1024 * 1024) == "1 MB"
    assert format_bytes(int(1.5 * 1024 * 1024)) == "1.5 MB"


def test_format_bytes_shows_gigabytes():
    assert format_bytes(1024 * 1024 * 1024) == "1 GB"


def test_format_bytes_negative_clamps_to_zero():
    assert format_bytes(-1) == "0 B"
