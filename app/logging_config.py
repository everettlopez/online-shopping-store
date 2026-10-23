"""One log format for the app and uvicorn: `time level logger message`, one line per
event, with details written as key=value pairs so they're easy to search in
`docker compose logs`. Log ids (order_id, product_id), not customers' emails or addresses.
"""
import logging
import re
import sys

from app.settings import DEFAULT_LOG_LEVEL, LOG_LEVELS, log_level

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")

# Request paths that carry a secret: an order's tracking token, a Checkout Session id
# (either one opens an order, with the buyer's name and address) and the tracking
# details an admin sends as query parameters
SECRET_QUERY = re.compile(r"([?&](?:token|tracking_number|tracking_url)=)[^&#]*")
SECRET_PATH = re.compile(r"(/payments/session/)[^/?#]+")


def redact_path(path: str) -> str:
    return SECRET_PATH.sub(r"\1REDACTED", SECRET_QUERY.sub(r"\1REDACTED", path))


class RedactSecrets(logging.Filter):
    """Keeps tokens out of the access log, which records every request's full path."""

    def filter(self, record):
        # uvicorn.access logs (client, method, path, http version, status)
        if isinstance(record.args, tuple) and len(record.args) == 5 and isinstance(record.args[2], str):
            record.args = (*record.args[:2], redact_path(record.args[2]), *record.args[3:])
        return True


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
    # Records from loggers with their own level (uvicorn's) skip the root's level
    handler.setLevel(level)

    # The startup schema check runs Alembic, which reports every plugin it loads
    logging.getLogger("alembic").setLevel(logging.DEBUG if level == "DEBUG" else logging.WARNING)

    # Uvicorn sets up its own handlers and levels before importing the app; route them
    # through ours, at LOG_LEVEL
    for name in UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.setLevel(logging.NOTSET)
        uvicorn_logger.propagate = True

    access_logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, RedactSecrets) for f in access_logger.filters):
        access_logger.addFilter(RedactSecrets())
