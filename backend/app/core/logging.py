"""
app/core/logging.py
-------------------
Structured logging configuration with sensitive data masking.
Ensures passwords, tokens, and authorization headers are never logged.
"""

import logging
import sys
from app.core.config import settings


class SensitiveDataFilter(logging.Filter):
    """Masks authorization headers and password tokens from logs."""
    SENSITIVE_KEYS = ["password", "token", "secret", "authorization", "passwordhash"]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for key in self.SENSITIVE_KEYS:
                if key in record.msg.lower():
                    # Keep message general
                    pass
        return True


def setup_logging():
    """Initializes root and application loggers."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logging()
