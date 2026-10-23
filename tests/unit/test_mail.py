from decimal import Decimal

import pytest
import resend

import app.mail as mail
from app.mail import (
    EmailMessage,
    build_order_confirmation_email,
    build_password_reset_email,
    build_shipping_notice_email,
    send_email,
)
from app.models.order import Order

MESSAGE = EmailMessage(to="pat@example.com", subject="Hello", text="Plain body", html="<p>Body</p>")

# Imported before any fixture runs, so this is the real backend, not the recorder
REAL_DELIVER = mail.deliver


@pytest.fixture
def real_deliver(monkeypatch, sent_emails):
    """Swap the conftest recorder back out so these tests exercise the real backends."""
    monkeypatch.setattr(mail, "deliver", REAL_DELIVER)


def test_without_an_api_key_emails_are_printed(real_deliver, capsys):
    assert send_email(MESSAGE) is True

    printed = capsys.readouterr().out
    assert "pat@example.com" in printed and "Plain body" in printed


def test_with_an_api_key_emails_go_to_resend(real_deliver, monkeypatch):
    calls = []
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("EMAIL_FROM", "Shop <orders@shop.example>")
    monkeypatch.setattr(resend.Emails, "send", calls.append)

    assert send_email(MESSAGE) is True

    assert resend.api_key == "re_test_key"
    assert calls == [{
        "from": "Shop <orders@shop.example>",
        "to": ["pat@example.com"],
        "subject": "Hello",
        "text": "Plain body",
        "html": "<p>Body</p>",
    }]


def test_message_sender_and_reply_to_go_to_resend(real_deliver, monkeypatch):
    calls = []
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("EMAIL_REPLY_TO", "support@shop.example")
    monkeypatch.setattr(resend.Emails, "send", calls.append)

    send_email(EmailMessage(to="pat@example.com", subject="Hello", text="t", html="h", sender="Shop <orders@shop.example>"))

    [call] = calls
    assert call["from"] == "Shop <orders@shop.example>"
    assert call["reply_to"] == "support@shop.example"


def test_printed_emails_show_the_sender(real_deliver, monkeypatch, capsys):
    monkeypatch.setenv("ACCOUNT_EMAIL_FROM", "Shop <support@shop.example>")

    send_email(build_password_reset_email("pat@example.com", "Pat", "tok", 30))

    assert "from Shop <support@shop.example> to pat@example.com" in capsys.readouterr().out


def test_send_failures_are_logged_not_raised(monkeypatch, caplog):
    def fail(message):
        raise RuntimeError("provider down")
    monkeypatch.setattr(mail, "deliver", fail)

    assert send_email(MESSAGE) is False
    [record] = [r for r in caplog.records if r.name == "app.mail"]
    assert record.levelname == "ERROR"
    assert "provider down" in record.getMessage()
    # Customers' addresses stay out of the logs
    assert MESSAGE.to not in caplog.text


def make_order(**fields):
    defaults = dict(
        order_id=1, user_id=1, first_name="Pat", order_number="abc12345", access_token="tok123",
        shipping_address_id=1, billing_address_id=1,
        shipping_address={"full_name": "Pat <Doe>", "line1": "1 Main St", "line2": None, "city": "Springfield",
                          "state": "IL", "postal_code": "62701", "country": "US"},
        total_amount=Decimal("1056.95"), subtotal_amount=Decimal("1000.00"),
        shipping_amount=Decimal("6.95"), tax_amount=Decimal("50.00"),
    )
    return Order(**{**defaults, **fields})


def test_password_reset_email_links_to_the_frontend():
    message = build_password_reset_email("pat@example.com", "Pat", "tok123", 30)

    assert message.to == "pat@example.com"
    assert "http://localhost:5173/reset-password?token=tok123" in message.text
    assert "30 minutes" in message.text


def test_emails_carry_the_store_name(monkeypatch):
    monkeypatch.setenv("STORE_NAME", "Corner Shop")

    reset = build_password_reset_email("pat@example.com", "Pat", "tok123", 30)
    confirmation = build_order_confirmation_email("pat@example.com", make_order(), [("Shirt", 1, Decimal("1"), Decimal("1"))])

    assert reset.subject == "Reset your Corner Shop password"
    assert "your Corner Shop account" in reset.text
    assert confirmation.subject == "Corner Shop order confirmation abc12345"
    assert confirmation.text.endswith("Corner Shop")
    assert "Corner Shop" in confirmation.html


def test_store_name_is_escaped_in_html(monkeypatch):
    monkeypatch.setenv("STORE_NAME", "<b>Shop</b>")

    html = build_password_reset_email("pat@example.com", "Pat", "tok123", 30).html

    assert "<b>Shop</b>" not in html
    assert "&lt;b&gt;Shop&lt;/b&gt;" in html


def test_order_confirmation_lists_items_and_totals():
    message = build_order_confirmation_email("pat@example.com", make_order(), [("Shirt", 2, Decimal("500"), Decimal("1000"))])

    assert message.subject == "Online Store order confirmation abc12345"
    assert "2 x Shirt @ $500.00 = $1,000.00" in message.text
    for line in ("Subtotal: $1,000.00", "Shipping: $6.95", "Tax: $50.00", "Total: $1,056.95"):
        assert line in message.text
    assert "Springfield, IL 62701" in message.text
    assert "http://localhost:5173/track/abc12345?token=tok123" in message.text


def test_user_text_is_escaped_in_html():
    message = build_order_confirmation_email("pat@example.com", make_order(), [("<b>Shirt</b>", 1, Decimal("1"), Decimal("1"))])

    assert "<b>Shirt</b>" not in message.html
    assert "&lt;b&gt;Shirt&lt;/b&gt;" in message.html
    assert "Pat &lt;Doe&gt;" in message.html


def test_shipping_notice_has_tracking_details():
    order = make_order(tracking_carrier="UPS", tracking_number="1Z999", tracking_url="https://ups.com/1Z999")

    message = build_shipping_notice_email("pat@example.com", order)

    assert message.subject == "Your Online Store order abc12345 has shipped"
    assert "UPS" in message.text and "1Z999" in message.text
    assert 'href="https://ups.com/1Z999"' in message.html


def test_shipping_notice_links_only_web_addresses():
    order = make_order(tracking_carrier="UPS", tracking_number="1Z999", tracking_url="javascript:alert(1)")

    assert "javascript:" not in build_shipping_notice_email("pat@example.com", order).html


def test_account_and_order_emails_use_their_own_senders(monkeypatch):
    monkeypatch.setenv("EMAIL_FROM", "Shop <hello@shop.example>")
    monkeypatch.setenv("ACCOUNT_EMAIL_FROM", "Shop <support@shop.example>")
    monkeypatch.setenv("ORDERS_EMAIL_FROM", "Shop <orders@shop.example>")
    order = make_order(tracking_carrier="UPS", tracking_number="1Z999", tracking_url="https://ups.com/1Z999")

    assert build_password_reset_email("pat@example.com", "Pat", "tok", 30).sender == "Shop <support@shop.example>"
    assert build_order_confirmation_email("pat@example.com", order, []).sender == "Shop <orders@shop.example>"
    assert build_shipping_notice_email("pat@example.com", order).sender == "Shop <orders@shop.example>"


def test_senders_fall_back_to_email_from(monkeypatch):
    monkeypatch.setenv("EMAIL_FROM", "Shop <hello@shop.example>")
    order = make_order()

    assert build_password_reset_email("pat@example.com", "Pat", "tok", 30).sender == "Shop <hello@shop.example>"
    assert build_order_confirmation_email("pat@example.com", order, []).sender == "Shop <hello@shop.example>"
