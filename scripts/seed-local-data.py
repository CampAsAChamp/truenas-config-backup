#!/usr/bin/env python3
"""Seed local dev data for the TrueNAS Config Backup dashboard.

Steps:
1. Resolve BACKUP_DIR and CONFIG_DIR from env (local-friendly defaults).
2. Optionally skip when backups already exist (--if-empty) or clear first (--force).
3. Write sample .tar backup files with realistic names and sizes.
4. Write history.jsonl with matching success and failure run entries.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BACKUP_DIR = REPO_ROOT / "local-data" / "backups"
DEFAULT_CONFIG_DIR = REPO_ROOT / "local-data" / "config"

# (UTC timestamp for filename, payload size in bytes)
BACKUP_SPECS: list[tuple[str, int]] = [
    ("20250504-030000", 512 * 1024),
    ("20250615-030000", 768 * 1024),
    ("20250706-030000", 1024 * 1024),
    ("20250720-030000", 2 * 1024 * 1024),
]

HISTORY_SPECS: list[dict] = [
    {
        "timestamp": "2025-05-04T02:58:12+00:00",
        "success": False,
        "message": "api down",
        "filename": None,
    },
    {
        "timestamp": "2025-05-04T03:00:00+00:00",
        "success": True,
        "message": "backup completed",
        "filename": "truenas-config-20250504-030000.tar",
    },
    {
        "timestamp": "2025-06-15T03:00:00+00:00",
        "success": True,
        "message": "backup completed",
        "filename": "truenas-config-20250615-030000.tar",
    },
    {
        "timestamp": "2025-07-01T03:00:00+00:00",
        "success": False,
        "message": "unexpected error: connection reset",
        "filename": None,
    },
    {
        "timestamp": "2025-07-06T03:00:00+00:00",
        "success": True,
        "message": "backup completed",
        "filename": "truenas-config-20250706-030000.tar",
    },
    {
        "timestamp": "2025-07-20T03:00:00+00:00",
        "success": True,
        "message": "backup completed",
        "filename": "truenas-config-20250720-030000.tar",
    },
]


def log_step(message: str) -> None:
    print(f"[*] {message}", file=sys.stderr)


def resolve_dirs() -> tuple[Path, Path]:
    """Resolve backup and config directories from env or local defaults."""
    backup_dir = Path(os.environ.get("BACKUP_DIR", DEFAULT_BACKUP_DIR))
    config_dir = Path(os.environ.get("CONFIG_DIR", DEFAULT_CONFIG_DIR))
    return backup_dir, config_dir


def has_backups(backup_dir: Path) -> bool:
    """Return True when BACKUP_DIR contains at least one .tar file."""
    if not backup_dir.is_dir():
        return False
    return any(path.suffix == ".tar" for path in backup_dir.iterdir())


def clear_existing(backup_dir: Path, history_file: Path) -> None:
    """Remove existing seed targets so --force can start clean."""
    if backup_dir.is_dir():
        for path in backup_dir.glob("*.tar"):
            path.unlink()
    if history_file.is_file():
        history_file.unlink()


def _parse_stamp(stamp: str) -> datetime:
    return datetime.strptime(stamp, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)


def write_backup_tar(path: Path, stamp: str, payload_size: int) -> None:
    """Write a minimal valid tar archive with a padded payload file."""
    mtime = _parse_stamp(stamp).timestamp()
    payload = b"local-dev seed data\n" + (b"x" * max(0, payload_size - 20))

    with tarfile.open(path, "w") as tar:
        info = tarfile.TarInfo(name="freenas-v1.db")
        info.size = len(payload)
        info.mtime = int(mtime)
        tar.addfile(info, io.BytesIO(payload))

    os.utime(path, (mtime, mtime))


def write_backups(backup_dir: Path) -> list[str]:
    """Create sample backup archives; returns filenames written."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    filenames: list[str] = []
    for stamp, payload_size in BACKUP_SPECS:
        filename = f"truenas-config-{stamp}.tar"
        write_backup_tar(backup_dir / filename, stamp, payload_size)
        filenames.append(filename)
    return filenames


def write_history(config_dir: Path) -> None:
    """Write run history JSONL (oldest-first; app reverses on read)."""
    config_dir.mkdir(parents=True, exist_ok=True)
    history_file = config_dir / "history.jsonl"
    with history_file.open("w") as f:
        for entry in HISTORY_SPECS:
            f.write(json.dumps(entry) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed local dev backup files and run history for dashboard testing.",
    )
    parser.add_argument(
        "--if-empty",
        action="store_true",
        default=True,
        help="Skip when BACKUP_DIR already contains .tar files (default).",
    )
    parser.add_argument(
        "--no-if-empty",
        action="store_false",
        dest="if_empty",
        help="Seed even when backups already exist (unless --force clears first).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing .tar backups and history.jsonl before seeding.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backup_dir, config_dir = resolve_dirs()
    history_file = config_dir / "history.jsonl"

    log_step(f"Backup dir: {backup_dir}")
    log_step(f"Config dir: {config_dir}")

    if args.force:
        log_step("Clearing existing local dev data")
        clear_existing(backup_dir, history_file)
    elif args.if_empty and has_backups(backup_dir):
        log_step("Backups already present; skipping seed (--if-empty)")
        return

    log_step(f"Writing {len(BACKUP_SPECS)} sample backup files")
    filenames = write_backups(backup_dir)

    log_step(f"Writing {len(HISTORY_SPECS)} history entries")
    write_history(config_dir)

    log_step(f"Done. Seeded: {', '.join(filenames)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log_step(f"Failed: {exc}")
        sys.exit(1)
