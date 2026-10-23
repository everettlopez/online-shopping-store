"""Email alerts to the store owner (ALERT_EMAIL) about problems that need a person: an
item sold twice, a webhook that failed, a Stripe error, a server error.

Each alert has a key naming the problem; repeats of a key within 15 minutes are held
back, so a problem that happens on every request sends one email, not hundreds. Like
the rate limits, this is kept in the process's memory, so each uvicorn worker holds
back its own repeats. Run `python -m app.alerts` to send a test alert.
"""
import logging
import sys
import threading
import time

from fastapi import BackgroundTasks

from app.mail import build_alert_email, send_email
from app.settings import alert_email

REPEAT_SECONDS = 15 * 60

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_last_sent: dict[str, float] = {}


def reset_alerts():
    """Forget which alerts were sent (tests start each case with a clean slate)."""
    with _lock:
        _last_sent.clear()


def alert_admin(key: str, subject: str, details: list[str], background_tasks: BackgroundTasks | None = None) -> bool:
    """Email the store owner, unless ALERT_EMAIL is empty or the same key was sent in
    the last 15 minutes. With background_tasks, it goes out after the response.
    Returns whether an email was queued or sent."""
    to = alert_email()
    if not to:
        return False

    now = time.monotonic()
    with _lock:
        last = _last_sent.get(key)
        if last is not None and now - last < REPEAT_SECONDS:
            logger.info("alert held back key=%s", key)
            return False
        _last_sent[key] = now

    message = build_alert_email(to, subject, details)
    logger.info("alert sent key=%s", key)
    if background_tasks is not None:
        background_tasks.add_task(send_email, message)
    else:
        send_email(message)
    return True


def main() -> int:
    if not alert_email():
        print("ALERT_EMAIL is not set, so there's nowhere to send alerts.")
        return 1
    message = build_alert_email(alert_email(), "Test alert", ["This is a test. Alerts from your store will arrive like this."])
    if not send_email(message):
        print("Sending the test alert failed; the error is above.")
        return 1
    print(f"Sent a test alert to {alert_email()}. If it doesn't arrive, check Resend's email log.")
    return 0


if __name__ == "__main__":
    from app.logging_config import configure_logging
    configure_logging()
    sys.exit(main())
