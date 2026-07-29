import os
from typing import Literal

from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel


def _str_env_from(name: str, env: dict[str, str], default: str = "") -> str:
    value = env.get(name)
    if value is None:
        return default
    return value.strip()


def _bool_env_from(name: str, env: dict[str, str], default: bool) -> bool:
    value = env.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def resolve_notify_provider(url: str, explicit: str) -> Literal["generic", "discord"]:
    if explicit and explicit != "generic":
        return explicit  # type: ignore[return-value]
    if "discord.com/api/webhooks" in url:
        return "discord"
    return "generic"


class TrueNasSettings(BaseModel):
    url: str = "https://127.0.0.1"
    api_key: str = ""
    verify_ssl: bool = False


class BackupSettings(BaseModel):
    dir: str = "/backups"
    cron_schedule: str = ""
    retention_count: int = 8
    include_secret_seed: bool = True
    include_pool_keys: bool = False
    include_root_authorized_keys: bool = False


class NotifySettings(BaseModel):
    webhook_url: str = ""
    provider: str = "generic"
    on_success: bool = False

    @property
    def effective_provider(self) -> Literal["generic", "discord"]:
        return resolve_notify_provider(self.webhook_url, self.provider)


class DisplaySettings(BaseModel):
    date_format: str = "mm/dd/yy"
    clock_format: Literal["12h", "24h"] = "12h"
    timezone_mode: Literal["local", "utc", "manual"] = "local"
    timezone: str = ""


class LoggingSettings(BaseModel):
    level: str = "INFO"
    file: str = ""
    max_bytes: int = 1_048_576
    backup_count: int = 3
    tail_limit: int = 200


class Settings(BaseModel):
    truenas: TrueNasSettings
    backup: BackupSettings
    notify: NotifySettings
    display: DisplaySettings
    logging: LoggingSettings
    dashboard_password: str = ""
    dashboard_page_size: int = 20
    web_port: int = 8080
    config_dir: str = "/config"
    health_check_truenas: bool = False
    dev_mode: bool = False

    @property
    def history_file(self) -> str:
        return os.path.join(self.config_dir, "history.jsonl")


def validate_settings(s: Settings) -> None:
    if not s.dashboard_password:
        raise ValueError("DASHBOARD_PASSWORD is required")

    if s.backup.retention_count < 0:
        raise ValueError(f"RETENTION_COUNT must be >= 0, got {s.backup.retention_count}")

    if s.dashboard_page_size < 1:
        raise ValueError(
            f"DASHBOARD_PAGE_SIZE must be >= 1, got {s.dashboard_page_size}"
        )

    if s.notify.provider not in ("generic", "discord"):
        raise ValueError(
            f"NOTIFY_PROVIDER must be 'generic' or 'discord', got {s.notify.provider!r}"
        )

    if s.backup.cron_schedule:
        CronTrigger.from_crontab(s.backup.cron_schedule)


def load_settings_from_env(environ: dict[str, str] | None = None) -> Settings:
    env = environ if environ is not None else os.environ
    config_dir = env.get("CONFIG_DIR", "/config")
    log_file = env.get("LOG_FILE", os.path.join(config_dir, "app.log"))

    notify_provider = _str_env_from("NOTIFY_PROVIDER", env, "generic").lower()

    display_clock = _str_env_from("DISPLAY_CLOCK_FORMAT", env, "12h").lower()
    if display_clock not in ("12h", "24h"):
        display_clock = "12h"

    display_tz_mode = _str_env_from("DISPLAY_TIMEZONE_MODE", env, "local").lower()
    if display_tz_mode not in ("local", "utc", "manual"):
        display_tz_mode = "local"

    return Settings(
        truenas=TrueNasSettings(
            url=_str_env_from("TRUENAS_URL", env, "https://127.0.0.1").rstrip("/"),
            api_key=_str_env_from("TRUENAS_API_KEY", env),
            verify_ssl=_bool_env_from("TRUENAS_VERIFY_SSL", env, False),
        ),
        backup=BackupSettings(
            dir=env.get("BACKUP_DIR", "/backups"),
            cron_schedule=_str_env_from("CRON_SCHEDULE", env),
            retention_count=int(env.get("RETENTION_COUNT", "8")),
            include_secret_seed=_bool_env_from("INCLUDE_SECRET_SEED", env, True),
            include_pool_keys=_bool_env_from("INCLUDE_POOL_KEYS", env, False),
            include_root_authorized_keys=_bool_env_from(
                "INCLUDE_ROOT_AUTHORIZED_KEYS", env, False
            ),
        ),
        notify=NotifySettings(
            webhook_url=_str_env_from("NOTIFY_WEBHOOK_URL", env),
            provider=notify_provider,
            on_success=_bool_env_from("NOTIFY_ON_SUCCESS", env, False),
        ),
        display=DisplaySettings(
            date_format=_str_env_from("DISPLAY_DATE_FORMAT", env, "mm/dd/yy"),
            clock_format=display_clock,  # type: ignore[arg-type]
            timezone_mode=display_tz_mode,  # type: ignore[arg-type]
            timezone=_str_env_from("DISPLAY_TIMEZONE", env),
        ),
        logging=LoggingSettings(
            level=_str_env_from("LOG_LEVEL", env, "INFO"),
            file=log_file,
            max_bytes=int(env.get("LOG_MAX_BYTES", "1048576")),
            backup_count=int(env.get("LOG_BACKUP_COUNT", "3")),
            tail_limit=int(env.get("LOG_TAIL_LIMIT", "200")),
        ),
        dashboard_password=_str_env_from("DASHBOARD_PASSWORD", env),
        dashboard_page_size=int(env.get("DASHBOARD_PAGE_SIZE", "20")),
        web_port=int(env.get("WEB_PORT", "8080")),
        config_dir=config_dir,
        health_check_truenas=_bool_env_from("HEALTH_CHECK_TRUENAS", env, False),
        dev_mode=_bool_env_from("DEV_MODE", env, False),
    )
