import logging

from apscheduler.triggers.cron import CronTrigger

from . import config

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
