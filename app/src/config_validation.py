import logging

from apscheduler.triggers.cron import CronTrigger

from . import config
from .settings import validate_settings

logger = logging.getLogger("truenas_config_backup")


def validate_config() -> None:
    if not config.DASHBOARD_PASSWORD:
        raise ValueError("DASHBOARD_PASSWORD is required")

    if not config.TRUENAS_API_KEY:
        logger.warning("TRUENAS_API_KEY is not set; backups will fail until configured")

    if config.RETENTION_COUNT < 0:
        raise ValueError(f"RETENTION_COUNT must be >= 0, got {config.RETENTION_COUNT}")

    if config.RETENTION_COUNT == 0:
        logger.warning("RETENTION_COUNT is 0; old backups will not be pruned")

    if config.CRON_SCHEDULE:
        CronTrigger.from_crontab(config.CRON_SCHEDULE)

    if config.DASHBOARD_PAGE_SIZE < 1:
        raise ValueError(f"DASHBOARD_PAGE_SIZE must be >= 1, got {config.DASHBOARD_PAGE_SIZE}")

    if config.settings.notify.provider not in ("generic", "discord"):
        raise ValueError(f"NOTIFY_PROVIDER must be 'generic' or 'discord', got {config.settings.notify.provider!r}")


def validate_loaded_settings() -> None:
    validate_settings(config.settings)
