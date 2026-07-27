import os


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


TRUENAS_URL = os.environ.get("TRUENAS_URL", "https://127.0.0.1").rstrip("/")
TRUENAS_API_KEY = os.environ.get("TRUENAS_API_KEY", "")
TRUENAS_VERIFY_SSL = _bool_env("TRUENAS_VERIFY_SSL", False)

BACKUP_DIR = os.environ.get("BACKUP_DIR", "/backups")
CONFIG_DIR = os.environ.get("CONFIG_DIR", "/config")

CRON_SCHEDULE = os.environ.get("CRON_SCHEDULE", "0 3 * * 0")
RETENTION_COUNT = int(os.environ.get("RETENTION_COUNT", "8"))
INCLUDE_SECRET_SEED = _bool_env("INCLUDE_SECRET_SEED", True)

WEB_PORT = int(os.environ.get("WEB_PORT", "8080"))

HISTORY_FILE = os.path.join(CONFIG_DIR, "history.jsonl")
