import json

from app import history


def test_append_and_read_all_round_trip(app_dirs):
    history.append(success=True, message="first", filename="a.tar")
    history.append(success=False, message="second")

    entries = history.read_all()

    assert len(entries) == 2
    assert entries[0]["message"] == "second"
    assert entries[0]["success"] is False
    assert entries[1]["message"] == "first"
    assert entries[1]["success"] is True
    assert entries[1]["filename"] == "a.tar"


def test_read_all_missing_file(app_dirs):
    assert history.read_all() == []


def test_read_all_skips_blank_and_malformed_lines(app_dirs):
    history_file = app_dirs["config_dir"] / "history.jsonl"
    history_file.write_text(
        '{"timestamp": "t1", "success": true, "message": "ok", "filename": null}\n'
        "\n"
        "not-json\n"
        '{"timestamp": "t2", "success": false, "message": "bad", "filename": null}\n'
    )

    entries = history.read_all()

    assert len(entries) == 2
    assert entries[0]["message"] == "bad"
    assert entries[1]["message"] == "ok"


def test_append_writes_jsonl(app_dirs):
    history.append(success=True, message="logged")

    lines = (app_dirs["config_dir"] / "history.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["success"] is True
    assert entry["message"] == "logged"
    assert "timestamp" in entry
