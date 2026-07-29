from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parent / "VERSION"


def get_version() -> str:
    try:
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "dev"


def get_display_version(*, dev_mode: bool = False) -> str:
    version = get_version()
    if dev_mode:
        return f"Local ({version})"
    return f"v{version}"
