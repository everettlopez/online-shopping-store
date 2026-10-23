"""One log format for the app and uvicorn: `time level logger message`, one line per
event, with details written as key=value pairs so they're easy to search in
`docker compose logs`. Log ids (order_id, product_id), not customers' emails or addresses.
"""
import logging
import sys

from app.settings import DEFAULT_LOG_LEVEL, LOG_LEVELS, log_level

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


def configure_logging():
    """Send the app's and uvicorn's logs to stderr in LOG_FORMAT, at LOG_LEVEL. Safe to
    call more than once (each uvicorn worker, and tests, build the app again)."""
    level = log_level()
    if level not in LOG_LEVELS:
        level = DEFAULT_LOG_LEVEL   # the startup check reports the bad value

    root = logging.getLogger()
    handler = next((h for h in root.handlers if getattr(h, "_store_handler", False)), None)
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)
        handler._store_handler = True
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root.addHandler(handler)
    root.setLevel(level)

    # The startup schema check runs Alembic, which reports every plugin it loads
    logging.getLogger("alembic").setLevel(logging.DEBUG if level == "DEBUG" else logging.WARNING)

    # Uvicorn sets up its own handlers before importing the app; route them through ours
    for name in UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
