import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed-local-data.py"


def _load_seed_module():
    spec = importlib.util.spec_from_file_location("seed_local_data", SEED_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _run_seed(
    tmp_path: Path,
    *,
    extra_args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    backup_dir = tmp_path / "backups"
    config_dir = tmp_path / "config"
    run_env = {
        **os.environ,
        "BACKUP_DIR": str(backup_dir),
        "CONFIG_DIR": str(config_dir),
        **(env or {}),
    }
    return subprocess.run(
        [sys.executable, str(SEED_SCRIPT), *(extra_args or [])],
        capture_output=True,
        text=True,
        env=run_env,
        check=False,
    )


def test_seed_creates_backups_and_history(tmp_path):
    result = _run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    backup_dir = tmp_path / "backups"
    config_dir = tmp_path / "config"
    history_file = config_dir / "history.jsonl"

    tar_files = sorted(backup_dir.glob("*.tar"))
    assert len(tar_files) == 4
    assert all(name.startswith("truenas-config-") for name in (p.name for p in tar_files))

    assert history_file.is_file()
    entries = [json.loads(line) for line in history_file.read_text().splitlines()]
    assert len(entries) == 6
    assert sum(1 for entry in entries if entry["success"]) == 4
    assert sum(1 for entry in entries if not entry["success"]) == 2


def test_seed_if_empty_skips_when_backups_exist(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True)
    (backup_dir / "existing.tar").write_bytes(b"keep")

    result = _run_seed(tmp_path, extra_args=["--if-empty"])

    assert result.returncode == 0, result.stderr
    assert "skipping seed" in result.stderr.lower()
    assert list(backup_dir.glob("*.tar")) == [backup_dir / "existing.tar"]
    assert not (tmp_path / "config" / "history.jsonl").exists()


def test_seed_force_replaces_existing_data(tmp_path):
    backup_dir = tmp_path / "backups"
    config_dir = tmp_path / "config"
    backup_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    (backup_dir / "old.tar").write_bytes(b"old")
    (config_dir / "history.jsonl").write_text('{"timestamp": "t", "success": true, "message": "old", "filename": null}\n')

    result = _run_seed(tmp_path, extra_args=["--force"])

    assert result.returncode == 0, result.stderr
    tar_files = sorted(backup_dir.glob("*.tar"))
    assert len(tar_files) == 4
    assert (backup_dir / "old.tar") not in tar_files

    entries = [json.loads(line) for line in (config_dir / "history.jsonl").read_text().splitlines()]
    assert len(entries) == 6
    assert entries[0]["message"] != "old"


def test_has_backups(tmp_path):
    seed = _load_seed_module()
    backup_dir = tmp_path / "backups"

    assert seed.has_backups(backup_dir) is False

    backup_dir.mkdir()
    assert seed.has_backups(backup_dir) is False

    (backup_dir / "notes.txt").write_text("skip")
    assert seed.has_backups(backup_dir) is False

    (backup_dir / "sample.tar").write_bytes(b"tar")
    assert seed.has_backups(backup_dir) is True
