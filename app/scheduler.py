import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config
from .backup_manager import run_backup

logger = logging.getLogger("truenas_config_backup")

_scheduler = BackgroundScheduler()


def start() -> None:
    trigger = CronTrigger.from_crontab(config.CRON_SCHEDULE)
    _scheduler.add_job(run_backup, trigger=trigger, id="scheduled_backup", replace_existing=True)
    _scheduler.start()
    logger.info("scheduler started with cron '%s'", config.CRON_SCHEDULE)


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


def next_run_time():
    job = _scheduler.get_job("scheduled_backup")
    return job.next_run_time if job else None
