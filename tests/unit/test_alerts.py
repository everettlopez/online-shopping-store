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


def test_a_bad_log_level_falls_back_to_info(root_logger, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "loud")

    configure_logging()

    assert root_logger.level == logging.INFO
