import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config
from .backup_manager import run_scheduled_backup

logger = logging.getLogger("truenas_config_backup")

_scheduler = BackgroundScheduler()


def start() -> None:
    if not config.CRON_SCHEDULE:
        logger.info("scheduler disabled (CRON_SCHEDULE not set)")
        return
    trigger = CronTrigger.from_crontab(config.CRON_SCHEDULE)
    _scheduler.add_job(
        run_scheduled_backup,
        trigger=trigger,
        id="scheduled_backup",
        replace_existing=True,
    )
    if not _scheduler.running:
        _scheduler.start()
    logger.info("scheduler started with cron '%s'", config.CRON_SCHEDULE)


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler stopped")


def reload() -> None:
    if _scheduler.running:
        _scheduler.remove_all_jobs()
    start()


def next_run_time():
    job = _scheduler.get_job("scheduled_backup")
    return job.next_run_time if job else None
