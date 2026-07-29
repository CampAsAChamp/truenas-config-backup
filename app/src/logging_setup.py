"""Central logging configuration for the application."""

from __future__ import annotations

import logging
import os
import time
from logging.handlers import RotatingFileHandler

from . import config

LOGGER_NAME = "truenas_config_backup"
LOG_DATEFMT = "%Y-%m-%dT%H:%M:%S"

_configured = False
_file_handler: RotatingFileHandler | None = None
_dev_access_filter_installed = False

DEV_QUIET_ACCESS_PATHS = (
    "/dev/boot-id",
    "/dev/asset-versions",
    "/dev/reload-state",
    "/dev/reload-events",
    "/api/logs",
)


class DevAccessLogFilter(logging.Filter):
    """Suppress high-frequency dev polling paths from uvicorn access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(path in message for path in DEV_QUIET_ACCESS_PATHS)


class UTCFormatter(logging.Formatter):
    """Format log timestamps in UTC with a +0000 suffix."""

    converter = time.gmtime

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        fmt = datefmt or LOG_DATEFMT
        return time.strftime(fmt, ct) + "+0000"


def _resolve_level() -> int:
    level_name = config.LOG_LEVEL.upper()
    return getattr(logging, level_name, logging.INFO)


def configure_logging() -> None:
    """Configure app logging once at startup."""
    global _configured, _file_handler
    if _configured:
        return

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(_resolve_level())
    logger.propagate = False

    formatter = UTCFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    os.makedirs(config.CONFIG_DIR, exist_ok=True)
    _file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    _file_handler.setFormatter(formatter)
    logger.addHandler(_file_handler)

    _configure_dev_access_logging()
    _configured = True


def _configure_dev_access_logging() -> None:
    """Hide noisy dev polling routes from uvicorn terminal access logs."""
    global _dev_access_filter_installed
    if not config.DEV_MODE or _dev_access_filter_installed:
        return
    logging.getLogger("uvicorn.access").addFilter(DevAccessLogFilter())
    _dev_access_filter_installed = True


def _remove_rotated_logs(path: str, backup_count: int) -> None:
    for index in range(1, backup_count + 1):
        rotated = f"{path}.{index}"
        if os.path.isfile(rotated):
            os.remove(rotated)


def clear_logs() -> None:
    """Truncate the log file and remove rotated backups."""
    path = os.path.abspath(config.LOG_FILE)
    logger = logging.getLogger(LOGGER_NAME)

    if _file_handler is not None and os.path.abspath(_file_handler.baseFilename) == path:
        _file_handler.acquire()
        try:
            if _file_handler.stream:
                _file_handler.stream.close()
                _file_handler.stream = None
            _remove_rotated_logs(_file_handler.baseFilename, _file_handler.backupCount)
            with open(_file_handler.baseFilename, "w", encoding=_file_handler.encoding):
                pass
            _file_handler.stream = _file_handler._open()
        finally:
            _file_handler.release()
    else:
        if os.path.isfile(path):
            with open(path, "w", encoding="utf-8"):
                pass
        _remove_rotated_logs(path, config.LOG_BACKUP_COUNT)

    logger.info("logs cleared")


def reset_for_tests() -> None:
    """Clear handlers so tests can reconfigure logging."""
    global _configured, _dev_access_filter_installed, _file_handler
    logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.filters = [filt for filt in access_logger.filters if not isinstance(filt, DevAccessLogFilter)]
    _configured = False
    _dev_access_filter_installed = False
    _file_handler = None
