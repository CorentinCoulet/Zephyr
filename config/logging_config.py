"""
Structured logging configuration for Zephyr Intelligence Platform.
"""

import logging
import sys
from typing import Optional


class _RequestIdFilter(logging.Filter):
    """Inject correlation request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from api.server import request_id_var
            record.request_id = request_id_var.get()
        except Exception:
            record.request_id = "-"
        return True


def setup_logging(level: Optional[str] = None, json_format: bool = False) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to INFO.
        json_format: If True, output JSON-formatted logs (for production).
    """
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)

    # Root logger for zephyr
    logger = logging.getLogger("zephyr")
    logger.setLevel(log_level)

    # Remove existing handlers to prevent duplicates
    logger.handlers.clear()

    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.addFilter(_RequestIdFilter())
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)


class JsonFormatter(logging.Formatter):
    """JSON log formatter for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)
