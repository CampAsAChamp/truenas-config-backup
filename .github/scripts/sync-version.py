#!/usr/bin/env python3
"""Sync release version across catalog files and VERSION."""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "ix-dev/community/truenas-config-backup"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <version>")

    version = sys.argv[1]

    (ROOT / "VERSION").write_text(f"{version}\n", encoding="utf-8")

    app_yaml = APP / "app.yaml"
    app_yaml.write_text(
        re.sub(
            r"^app_version: .*",
            f"app_version: {version}",
            app_yaml.read_text(encoding="utf-8"),
            count=1,
            flags=re.MULTILINE,
        ),
        encoding="utf-8",
    )

    ix_values = APP / "ix_values.yaml"
    ix_values.write_text(
        re.sub(
            r"(repository: ghcr\.io/campasachamp/truenas-config-backup\n    tag: ).*",
            rf"\g<1>{version}",
            ix_values.read_text(encoding="utf-8"),
            count=1,
        ),
        encoding="utf-8",
    )

    compose = APP / "templates/rendered/docker-compose.yaml"
    compose.write_text(
        re.sub(
            r"image: ghcr\.io/campasachamp/truenas-config-backup:.*",
            f"image: ghcr.io/campasachamp/truenas-config-backup:{version}",
            compose.read_text(encoding="utf-8"),
            count=1,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
