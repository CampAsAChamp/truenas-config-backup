import logging

from src import config
from src.logging_setup import (
    LOGGER_NAME,
    DevAccessLogFilter,
    clear_logs,
    configure_logging,
    reset_for_tests,
)


def test_configure_logging_writes_to_file(app_dirs, monkeypatch):
    log_file = app_dirs["config_dir"] / "app.log"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))
    monkeypatch.setattr(config, "LOG_LEVEL", "INFO")
    reset_for_tests()

    configure_logging()
    logger = logging.getLogger(LOGGER_NAME)
    logger.info("test message")

    for handler in logger.handlers:
        handler.flush()

    assert log_file.is_file()
    assert "test message" in log_file.read_text(encoding="utf-8")


def test_invalid_log_level_falls_back_to_info(app_dirs, monkeypatch):
    log_file = app_dirs["config_dir"] / "app.log"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))
    monkeypatch.setattr(config, "LOG_LEVEL", "NOT_A_LEVEL")
    reset_for_tests()

    configure_logging()
    logger = logging.getLogger(LOGGER_NAME)

    assert logger.level == logging.INFO


def test_clear_logs_truncates_file_and_rotated_backups(app_dirs, monkeypatch):
    log_file = app_dirs["config_dir"] / "app.log"
    rotated = app_dirs["config_dir"] / "app.log.1"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))
    monkeypatch.setattr(config, "LOG_BACKUP_COUNT", 3)
    reset_for_tests()

    configure_logging()
    log_file.write_text("old entry\n", encoding="utf-8")
    rotated.write_text("rotated entry\n", encoding="utf-8")

    clear_logs()

    assert log_file.read_text(encoding="utf-8").endswith("logs cleared\n")
    assert not rotated.exists()


def test_dev_access_log_filter_suppresses_noisy_paths():
    filt = DevAccessLogFilter()
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='127.0.0.1:8080 - "GET /dev/reload-state HTTP/1.1" 200',
        args=(),
        exc_info=None,
    )

    assert filt.filter(record) is False

    record.msg = '127.0.0.1:8080 - "GET /api/backups HTTP/1.1" 200'
    assert filt.filter(record) is True


def test_configure_logging_installs_dev_access_filter_in_dev_mode(app_dirs, monkeypatch):
    log_file = app_dirs["config_dir"] / "app.log"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))
    monkeypatch.setattr(config, "DEV_MODE", True)
    reset_for_tests()

    configure_logging()

    access_logger = logging.getLogger("uvicorn.access")
    assert any(isinstance(filt, DevAccessLogFilter) for filt in access_logger.filters)


def test_configure_logging_skips_dev_access_filter_outside_dev_mode(app_dirs, monkeypatch):
    log_file = app_dirs["config_dir"] / "app.log"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))
    monkeypatch.setattr(config, "DEV_MODE", False)
    reset_for_tests()

    configure_logging()

    access_logger = logging.getLogger("uvicorn.access")
    assert not any(isinstance(filt, DevAccessLogFilter) for filt in access_logger.filters)
