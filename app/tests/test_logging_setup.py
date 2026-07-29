import logging

from src import config
from src.logging_setup import LOGGER_NAME, configure_logging, reset_for_tests


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
