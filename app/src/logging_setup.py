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
    global _configured
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
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _configured = True


def reset_for_tests() -> None:
    """Clear handlers so tests can reconfigure logging."""
    global _configured
    logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    _configured = False
