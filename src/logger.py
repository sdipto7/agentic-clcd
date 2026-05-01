"""
Application-wide logging: console plus rotating-style single file under logs/.
"""

from __future__ import annotations

import logging
import os
from src.constants import LOG_FILE_PATH, LOGS_DIR

_CONFIGURED: bool = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure root logging once: timestamp | level | module | message.

    Writes logs to a single file under logs/. No console handler is attached.

    Args:
        level: Minimum log level for handlers.

    Returns:
        The root logger after configuration.
    """
    global _CONFIGURED
    root = logging.getLogger()
    if _CONFIGURED:
        return root

    os.makedirs(LOGS_DIR, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    root.setLevel(level)

    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    root.handlers.clear()
    root.addHandler(file_handler)

    _CONFIGURED = True

    return root


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger, ensuring setup has run at least once.

    Args:
        name: Logger name; pass ``__name__`` from the calling module.

    Returns:
        Configured Logger instance.
    """
    setup_logging()

    return logging.getLogger(name)
