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

CRON_SCHEDULE = os.environ.get("CRON_SCHEDULE", "").strip()
RETENTION_COUNT = int(os.environ.get("RETENTION_COUNT", "8"))
INCLUDE_SECRET_SEED = _bool_env("INCLUDE_SECRET_SEED", True)
INCLUDE_POOL_KEYS = _bool_env("INCLUDE_POOL_KEYS", False)
INCLUDE_ROOT_AUTHORIZED_KEYS = _bool_env("INCLUDE_ROOT_AUTHORIZED_KEYS", False)

WEB_PORT = int(os.environ.get("WEB_PORT", "8080"))
DASHBOARD_PAGE_SIZE = int(os.environ.get("DASHBOARD_PAGE_SIZE", "20"))

DISPLAY_DATE_FORMAT = os.environ.get("DISPLAY_DATE_FORMAT", "mm/dd/yy").strip()
DISPLAY_CLOCK_FORMAT = os.environ.get("DISPLAY_CLOCK_FORMAT", "12h").strip().lower()
DISPLAY_TIMEZONE_MODE = os.environ.get("DISPLAY_TIMEZONE_MODE", "local").strip().lower()
DISPLAY_TIMEZONE = os.environ.get("DISPLAY_TIMEZONE", "").strip()

DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "").strip()

NOTIFY_WEBHOOK_URL = os.environ.get("NOTIFY_WEBHOOK_URL", "").strip()
NOTIFY_PROVIDER = os.environ.get("NOTIFY_PROVIDER", "generic").strip().lower()
NOTIFY_ON_SUCCESS = _bool_env("NOTIFY_ON_SUCCESS", False)

HEALTH_CHECK_TRUENAS = _bool_env("HEALTH_CHECK_TRUENAS", False)

DEV_MODE = _bool_env("DEV_MODE", False)

HISTORY_FILE = os.path.join(CONFIG_DIR, "history.jsonl")
