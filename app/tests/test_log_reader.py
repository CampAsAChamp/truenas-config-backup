from src import config
from src.log_reader import tail_log_entries


def test_tail_log_entries_parses_lines(app_dirs, monkeypatch):
    log_file = app_dirs["config_dir"] / "app.log"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))
    log_file.write_text(
        "\n".join([
            "2026-07-29T10:45:00+0000 INFO truenas_config_backup: application starting",
            "2026-07-29T10:45:01+0000 WARNING truenas_config_backup: something odd",
            "unparseable legacy line",
        ]),
        encoding="utf-8",
    )

    entries = tail_log_entries(limit=10)

    assert len(entries) == 3
    assert entries[0]["timestamp"] == "2026-07-29T10:45:00Z"
    assert entries[0]["level"] == "INFO"
    assert entries[0]["message"] == "application starting"
    assert entries[1]["level"] == "WARNING"
    assert entries[2]["message"] == "unparseable legacy line"


def test_tail_log_entries_missing_file(app_dirs, monkeypatch):
    monkeypatch.setattr(config, "LOG_FILE", str(app_dirs["config_dir"] / "missing.log"))

    assert tail_log_entries() == []


def test_tail_log_entries_respects_limit(app_dirs, monkeypatch):
    log_file = app_dirs["config_dir"] / "app.log"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))
    monkeypatch.setattr(config, "LOG_TAIL_LIMIT", 2)
    log_file.write_text(
        "\n".join([
            "2026-07-29T10:45:00+0000 INFO truenas_config_backup: first",
            "2026-07-29T10:45:01+0000 INFO truenas_config_backup: second",
            "2026-07-29T10:45:02+0000 INFO truenas_config_backup: third",
        ]),
        encoding="utf-8",
    )

    entries = tail_log_entries(limit=2)

    assert len(entries) == 2
    assert entries[0]["message"] == "second"
    assert entries[1]["message"] == "third"
