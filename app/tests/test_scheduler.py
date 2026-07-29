from unittest.mock import MagicMock

from src import scheduler


def test_start_skips_when_no_schedule(monkeypatch):
    monkeypatch.setattr("src.config.CRON_SCHEDULE", "")
    add_job = MagicMock()
    start = MagicMock()
    monkeypatch.setattr(scheduler._scheduler, "add_job", add_job)
    monkeypatch.setattr(scheduler._scheduler, "start", start)

    scheduler.start()

    add_job.assert_not_called()
    start.assert_not_called()


def test_start_registers_job_when_schedule_set(monkeypatch):
    monkeypatch.setattr("src.config.CRON_SCHEDULE", "0 3 * * 0")
    add_job = MagicMock()
    start = MagicMock()
    monkeypatch.setattr(scheduler._scheduler, "add_job", add_job)
    monkeypatch.setattr(scheduler._scheduler, "start", start)

    scheduler.start()

    add_job.assert_called_once()
    start.assert_called_once()
