from .settings import Settings
from .settings_store import load_settings as _load_merged_settings


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    return _load_merged_settings(environ)


settings: Settings = load_settings()


def reload_settings(environ: dict[str, str] | None = None) -> Settings:
    global settings
    settings = load_settings(environ)
    _sync_module_aliases(settings)
    return settings


def _sync_module_aliases(s: Settings) -> None:
    global TRUENAS_URL, TRUENAS_API_KEY, TRUENAS_VERIFY_SSL
    global BACKUP_DIR, CONFIG_DIR, CRON_SCHEDULE, RETENTION_COUNT
    global INCLUDE_SECRET_SEED, INCLUDE_POOL_KEYS, INCLUDE_ROOT_AUTHORIZED_KEYS
    global WEB_PORT, DASHBOARD_PAGE_SIZE
    global DISPLAY_DATE_FORMAT, DISPLAY_CLOCK_FORMAT, DISPLAY_TIMEZONE_MODE, DISPLAY_TIMEZONE
    global DASHBOARD_PASSWORD
    global NOTIFY_WEBHOOK_URL, NOTIFY_PROVIDER, NOTIFY_ON_SUCCESS
    global HEALTH_CHECK_TRUENAS, DEV_MODE
    global LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT, LOG_TAIL_LIMIT
    global HISTORY_FILE

    TRUENAS_URL = s.truenas.url
    TRUENAS_API_KEY = s.truenas.api_key
    TRUENAS_VERIFY_SSL = s.truenas.verify_ssl

    BACKUP_DIR = s.backup.dir
    CRON_SCHEDULE = s.backup.cron_schedule
    RETENTION_COUNT = s.backup.retention_count
    INCLUDE_SECRET_SEED = s.backup.include_secret_seed
    INCLUDE_POOL_KEYS = s.backup.include_pool_keys
    INCLUDE_ROOT_AUTHORIZED_KEYS = s.backup.include_root_authorized_keys

    WEB_PORT = s.web_port
    DASHBOARD_PAGE_SIZE = s.dashboard_page_size

    DISPLAY_DATE_FORMAT = s.display.date_format
    DISPLAY_CLOCK_FORMAT = s.display.clock_format
    DISPLAY_TIMEZONE_MODE = s.display.timezone_mode
    DISPLAY_TIMEZONE = s.display.timezone

    DASHBOARD_PASSWORD = s.dashboard_password

    NOTIFY_WEBHOOK_URL = s.notify.webhook_url
    NOTIFY_PROVIDER = s.notify.effective_provider
    NOTIFY_ON_SUCCESS = s.notify.on_success

    HEALTH_CHECK_TRUENAS = s.health_check_truenas
    DEV_MODE = s.dev_mode

    CONFIG_DIR = s.config_dir
    LOG_LEVEL = s.logging.level
    LOG_FILE = s.logging.file
    LOG_MAX_BYTES = s.logging.max_bytes
    LOG_BACKUP_COUNT = s.logging.backup_count
    LOG_TAIL_LIMIT = s.logging.tail_limit

    HISTORY_FILE = s.history_file


_sync_module_aliases(settings)
