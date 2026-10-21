import stripe

from app.routes.payments import get_payment_details, summarize_payment_method


def test_summarize_card():
    pmd = {"type": "card", "card": {"brand": "visa", "last4": "4242", "wallet": None}}

    assert summarize_payment_method(pmd) == {
        "payment_method_type": "card",
        "card_brand": "visa",
        "card_last4": "4242",
    }


def test_summarize_wallet_shows_wallet_type():
    pmd = {"type": "card", "card": {"brand": "visa", "last4": "1111", "wallet": {"type": "apple_pay"}}}

    assert summarize_payment_method(pmd) == {
        "payment_method_type": "apple_pay",
        "card_brand": "visa",
        "card_last4": "1111",
    }


def test_summarize_card_funded_method():
    pmd = {"type": "amazon_pay", "amazon_pay": {"funding": {"card": {"brand": "mastercard", "last4": "5555"}}}}

    assert summarize_payment_method(pmd) == {
        "payment_method_type": "amazon_pay",
        "card_brand": "mastercard",
        "card_last4": "5555",
    }


def test_summarize_method_without_card():
    pmd = {"type": "klarna", "klarna": {}}

    assert summarize_payment_method(pmd) == {
        "payment_method_type": "klarna",
        "card_brand": None,
        "card_last4": None,
    }


def make_intent(charge):
    return stripe.PaymentIntent.construct_from({"id": "pi_123", "latest_charge": charge}, "sk_test")


def test_get_payment_details(monkeypatch):
    intent = make_intent({
        "id": "ch_123",
        "object": "charge",
        "status": "succeeded",
        "receipt_url": "https://pay.stripe.com/receipts/123",
        "payment_method_details": {"type": "card", "card": {"brand": "visa", "last4": "4242"}},
    })
    monkeypatch.setattr(stripe.PaymentIntent, "retrieve", lambda *args, **kwargs: intent)

    assert get_payment_details("pi_123") == {
        "payment_method_type": "card",
        "card_brand": "visa",
        "card_last4": "4242",
        "payment_status": "succeeded",
        "receipt_url": "https://pay.stripe.com/receipts/123",
    }


def test_get_payment_details_without_charge(monkeypatch):
    monkeypatch.setattr(stripe.PaymentIntent, "retrieve", lambda *args, **kwargs: make_intent(None))

    assert get_payment_details("pi_123") == {}


def test_get_payment_details_when_stripe_fails(monkeypatch):
    def fail(*args, **kwargs):
        raise stripe.error.APIConnectionError("network down")

    monkeypatch.setattr(stripe.PaymentIntent, "retrieve", fail)

    assert get_payment_details("pi_123") == {}
