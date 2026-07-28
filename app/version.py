from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parent / "VERSION"


def get_version() -> str:
    try:
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "dev"
