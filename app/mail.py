"""Customer emails: password reset, order confirmation and shipping notice.

Messages are built while the request still has the database (build_* functions)
and sent afterwards with send_email, usually from a BackgroundTask so the
customer and Stripe's webhook don't wait on the email provider.
"""
from dataclasses import dataclass
from decimal import Decimal
from html import escape
from urllib.parse import quote, urlencode

import resend

from app.models.order import Order
from app.settings import (
    account_email_from,
    email_from,
    email_reply_to,
    frontend_url,
    orders_email_from,
    resend_api_key,
    store_name,
)


@dataclass
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str
    sender: str | None = None   # None sends from EMAIL_FROM


def send_email(message: EmailMessage) -> bool:
    """Send a message. Failures are logged, never raised: a mail outage must not
    undo an order or stop an admin from saving tracking details."""
    try:
        deliver(message)
        return True
    except Exception as e:
        print("Failed to send email:", message.subject, "to", message.to, e)
        return False


def deliver(message: EmailMessage):
    api_key = resend_api_key()
    sender = message.sender or email_from()
    reply_to = email_reply_to()

    # Local development: show the email instead of sending it. Flushed so it shows
    # right away even when output is piped (a preview pane, Docker logs)
    if not api_key:
        print(
            f"--- Email from {sender} to {message.to}: {message.subject} ---\n{message.text}\n--- End of email ---",
            flush=True,
        )
        return

    params = {
        "from": sender,
        "to": [message.to],
        "subject": message.subject,
        "text": message.text,
        "html": message.html,
    }
    # Replies go to a real inbox (support), whichever address sent the email
    if reply_to:
        params["reply_to"] = reply_to

    resend.api_key = api_key
    resend.Emails.send(params)


# -----------------------------------------
# Message builders
# -----------------------------------------

def money(amount) -> str:
    return f"${Decimal(amount or 0):,.2f}"


def html_page(heading: str, body: str) -> str:
    return (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#111">'
        f'<h1 style="font-size:22px">{escape(heading)}</h1>{body}'
        f'<p style="color:#666;font-size:13px">{escape(store_name())}</p></div>'
    )


def signed(lines: list[str]) -> str:
    """Plain-text body ending with the store's name."""
    return "\n".join([*lines, "", store_name()])


def html_button(url: str, label: str) -> str:
    return (
        f'<p><a href="{escape(url)}" style="display:inline-block;background:#000;color:#fff;'
        f'padding:10px 20px;border-radius:999px;text-decoration:none">{escape(label)}</a></p>'
    )


def build_password_reset_email(to: str, first_name: str, token: str, minutes: int) -> EmailMessage:
    link = f"{frontend_url()}/reset-password?token={token}"
    store = store_name()
    text = signed([
        f"Hi {first_name},",
        "",
        f"Someone asked to reset the password for your {store} account. To choose a new one, "
        f"open this link within {minutes} minutes:",
        "",
        link,
        "",
        "If you didn't ask for this, you can ignore this email; your password stays the same.",
    ])
    html = html_page("Reset your password", (
        f"<p>Hi {escape(first_name)},</p>"
        f"<p>Someone asked to reset the password for your {escape(store)} account. The link works for {minutes} minutes.</p>"
        + html_button(link, "Choose a new password")
        + "<p>If you didn't ask for this, you can ignore this email; your password stays the same.</p>"
    ))
    return EmailMessage(to=to, subject=f"Reset your {store} password", text=text, html=html, sender=account_email_from())


def address_lines(address: dict | None) -> list[str]:
    if not address:
        return []
    city_line = f"{address['city']}, {address['state']} {address['postal_code']}"
    return [line for line in (address["full_name"], address["line1"], address.get("line2"), city_line) if line]


def order_link(order: Order) -> str:
    """The order's private tracking page, which opens without logging in (guests have
    no account), so the same link works for every buyer on any device."""
    query = urlencode({"token": order.access_token or ""})
    return f"{frontend_url()}/track/{quote(order.order_number)}?{query}"


def greeting(order: Order) -> str:
    return f"Hi {order.first_name}," if order.first_name else "Hi,"


def build_order_confirmation_email(to: str, order: Order, items: list[tuple[str, int, Decimal, Decimal]]) -> EmailMessage:
    """items: (product title, quantity, unit price paid, line subtotal)."""
    link = order_link(order)
    totals = [
        ("Subtotal", order.subtotal_amount),
        ("Shipping", order.shipping_amount),
        ("Tax", order.tax_amount),
        ("Total", order.total_amount),
    ]
    address = address_lines(order.shipping_address)

    text = signed([
        greeting(order),
        "",
        f"Thanks for your order! Order number: {order.order_number}",
        "",
        *[f"{quantity} x {title} @ {money(price)} = {money(subtotal)}" for title, quantity, price, subtotal in items],
        "",
        *[f"{label}: {money(amount)}" for label, amount in totals],
        "",
        "Shipping to:",
        *address,
        "",
        f"View your order: {link}",
    ])

    item_rows = "".join(
        f"<tr><td>{escape(title)} &times; {quantity}</td><td style=\"text-align:right\">{money(subtotal)}</td></tr>"
        for title, quantity, _, subtotal in items
    )
    total_rows = "".join(
        f"<tr><td>{label}</td><td style=\"text-align:right\">{money(amount)}</td></tr>"
        for label, amount in totals
    )
    html = html_page("Thanks for your order", (
        f"<p>{escape(greeting(order))} we've received your order "
        f"<strong>{escape(order.order_number)}</strong>.</p>"
        f'<table style="width:100%;border-collapse:collapse">{item_rows}'
        f'<tr><td colspan="2"><hr></td></tr>{total_rows}</table>'
        f"<p><strong>Shipping to</strong><br>{'<br>'.join(escape(line) for line in address)}</p>"
        + html_button(link, "View your order")
    ))
    return EmailMessage(to=to, subject=f"{store_name()} order confirmation {order.order_number}", text=text, html=html,
                        sender=orders_email_from())


def build_shipping_notice_email(to: str, order: Order) -> EmailMessage:
    link = order_link(order)
    text = signed([
        greeting(order),
        "",
        f"Your order {order.order_number} is on its way.",
        f"Carrier: {order.tracking_carrier}",
        f"Tracking number: {order.tracking_number}",
        f"Track your package: {order.tracking_url}",
        "",
        f"View your order: {link}",
    ])
    html = html_page("Your order has shipped", (
        f"<p>{escape(greeting(order))} your order <strong>{escape(order.order_number)}</strong> is on its way.</p>"
        f"<p>{escape(order.tracking_carrier or '')} tracking number: <strong>{escape(order.tracking_number or '')}</strong></p>"
        # Only web links become a button (the URL is typed in by an admin)
        + (html_button(order.tracking_url, "Track your package")
           if (order.tracking_url or "").lower().startswith(("https://", "http://")) else "")
        + f'<p><a href="{escape(link)}">View your order</a></p>'
    ))
    return EmailMessage(to=to, subject=f"Your {store_name()} order {order.order_number} has shipped", text=text, html=html,
                        sender=orders_email_from())
