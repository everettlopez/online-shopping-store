"""Email alerts to the store owner, and the log format."""
import logging

import pytest
from fastapi import BackgroundTasks

import app.alerts as alerts
from app.alerts import REPEAT_SECONDS, alert_admin
from app.logging_config import LOG_FORMAT, configure_logging


@pytest.fixture
def owner(monkeypatch):
    monkeypatch.setenv("ALERT_EMAIL", "owner@shop.example")
    monkeypatch.setenv("ORDERS_EMAIL_FROM", "Shop <orders@shop.example>")


@pytest.fixture
def clock(monkeypatch):
    """Control the time alerts see, in seconds."""
    now = [1000.0]
    monkeypatch.setattr(alerts.time, "monotonic", lambda: now[0])
    return now


def test_alerts_are_off_without_alert_email(sent_emails):
    assert alert_admin("oversold-1", "Oversold", ["details"]) is False
    assert sent_emails == []


def test_alert_email(owner, sent_emails):
    assert alert_admin("oversold-1", "Oversold: Shirt", ["Order abc paid for 2.", "Refund it."]) is True

    [message] = sent_emails
    assert message.to == "owner@shop.example"
    assert message.sender == "Shop <orders@shop.example>"
    assert message.subject == "[Online Store alert] Oversold: Shirt"
    assert "Order abc paid for 2.\nRefund it." in message.text
    assert "<p>Refund it.</p>" in message.html


def test_repeats_are_held_back_for_15_minutes(owner, clock, sent_emails):
    alert_admin("oversold-1", "Oversold", ["first"])
    clock[0] += REPEAT_SECONDS - 1
    assert alert_admin("oversold-1", "Oversold", ["again"]) is False
    # A different problem still gets through
    assert alert_admin("oversold-2", "Oversold", ["other product"]) is True

    clock[0] += 1
    assert alert_admin("oversold-1", "Oversold", ["later"]) is True
    assert [m.text.splitlines()[0] for m in sent_emails] == ["first", "other product", "later"]


def test_alert_can_wait_for_the_response(owner, sent_emails):
    tasks = BackgroundTasks()

    alert_admin("checkout-stripe-error", "Checkout is failing", ["details"], tasks)

    assert sent_emails == []
    assert len(tasks.tasks) == 1


def test_test_alert_command(owner, sent_emails, capsys):
    assert alerts.main() == 0

    [message] = sent_emails
    assert message.subject == "[Online Store alert] Test alert"
    assert "owner@shop.example" in capsys.readouterr().out


def test_test_alert_command_without_alert_email(sent_emails, capsys):
    assert alerts.main() == 1
    assert sent_emails == []
    assert "ALERT_EMAIL is not set" in capsys.readouterr().out


def test_test_alert_command_reports_a_failed_send(owner, monkeypatch, capsys):
    def fail(message):
        raise RuntimeError("provider down")
    monkeypatch.setattr("app.mail.deliver", fail)

    assert alerts.main() == 1
    assert "failed" in capsys.readouterr().out


# -----------------------------------------
# Logging
# -----------------------------------------

@pytest.fixture
def root_logger():
    root = logging.getLogger()
    level = root.level
    yield root
    root.setLevel(level)
    for handler in root.handlers:
        if getattr(handler, "_store_handler", False):
            handler.setLevel(level)


def test_logging_has_one_format_for_the_app_and_uvicorn(root_logger, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")
    logging.getLogger("uvicorn.access").addHandler(logging.StreamHandler())

    configure_logging()
    configure_logging()   # every worker builds the app again

    ours = [h for h in root_logger.handlers if getattr(h, "_store_handler", False)]
    assert len(ours) == 1
    assert ours[0].formatter._fmt == LOG_FORMAT
    assert root_logger.level == logging.DEBUG
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        assert logging.getLogger(name).handlers == []
        assert logging.getLogger(name).propagate


def test_log_level_quiets_uvicorn_too(root_logger, monkeypatch):
    # Uvicorn sets its loggers to INFO before the app is imported
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    configure_logging()

    [ours] = [h for h in root_logger.handlers if getattr(h, "_store_handler", False)]
    access = logging.getLogger("uvicorn.access")
    assert not access.isEnabledFor(logging.INFO)
    assert ours.level == logging.WARNING


def test_a_bad_log_level_falls_back_to_info(root_logger, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "loud")

    configure_logging()

    assert root_logger.level == logging.INFO


def test_access_log_leaves_out_order_secrets(root_logger, caplog):
    configure_logging()
    configure_logging()
    access = logging.getLogger("uvicorn.access")
    line = '%s - "%s %s HTTP/%s" %d'

    with caplog.at_level(logging.INFO):
        for path in ("/api/orders/track/ab12cd34ef56?token=secret-token",
                     "/api/payments/session/cs_live_secret",
                     "/api/orders/5/tracking?tracking_number=1Z999&tracking_carrier=UPS&tracking_url=https%3A%2F%2Fups.example",
                     "/api/products/active?size=M"):
            access.info(line, "203.0.113.5:4000", "GET", path, "1.1", 200)

    assert "secret" not in caplog.text and "1Z999" not in caplog.text and "ups.example" not in caplog.text
    assert "/api/orders/track/ab12cd34ef56?token=REDACTED" in caplog.text
    assert "/api/payments/session/REDACTED" in caplog.text
    assert "tracking_carrier=UPS" in caplog.text
    assert "/api/products/active?size=M" in caplog.text
    assert len(access.filters) == 1
