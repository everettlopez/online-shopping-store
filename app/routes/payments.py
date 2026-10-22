from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
import stripe
import uuid
import json
import os
from datetime import datetime

from app.db.session import get_session
from app.schemas.checkout import CheckoutRequest
from app.auth.core import CurrentUser
from app.settings import (
    automatic_tax_enabled,
    free_shipping_threshold,
    frontend_url,
    product_tax_code,
    shipping_flat_rate,
)
from app.money import from_cents, to_cents
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.address import Address
from app.schemas.address import address_snapshot
from app.routes.order import build_order_reads
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["Payments"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Stripe's tax code for shipping charges
SHIPPING_TAX_CODE = "txcd_92010001"


def shipping_cents(subtotal_cents: int) -> int:
    """Flat-rate shipping, free once the items reach the free-shipping threshold."""
    if subtotal_cents >= to_cents(free_shipping_threshold()):
        return 0
    return to_cents(shipping_flat_rate())


def stripe_address(address: Address) -> dict:
    return {
        "line1": address.line1,
        "line2": address.line2 or None,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
    }


def get_stripe_customer(session: Session, user: User, shipping: Address, billing: Address) -> str:
    """The user's Stripe Customer id, with its addresses set to this checkout's.
    Stripe Tax works out the sales tax from the customer's shipping address."""
    details = {
        "email": user.email,
        "name": f"{user.first_name} {user.last_name}",
        "address": stripe_address(billing),
        "shipping": {"name": shipping.full_name, "phone": shipping.phone, "address": stripe_address(shipping)},
    }

    if user.stripe_customer_id:
        try:
            stripe.Customer.modify(user.stripe_customer_id, **details)
            return user.stripe_customer_id
        except stripe.InvalidRequestError:
            # Deleted in Stripe, or created with other keys (sandbox vs live): make a new one
            pass

    customer = stripe.Customer.create(**details, metadata={"user_id": user.user_id})
    user.stripe_customer_id = customer.id
    session.add(user)
    session.commit()
    return customer.id


@router.get("/shipping")
def get_shipping_rates():
    """Shipping prices, so the checkout page can show them before payment."""
    return {"flat_rate": float(shipping_flat_rate()), "free_shipping_threshold": float(free_shipping_threshold())}


@router.post("/create-checkout-session")
def create_checkout_session(data: CheckoutRequest, user: CurrentUser, session: Session = Depends(get_session)):
    # 1. Load cart
    cart = session.exec(select(Cart).where(Cart.user_id == user.user_id)).first()
    if not cart:
        raise HTTPException(status_code=400, detail="Cart not found")

    cart_items = session.exec(select(CartItem).where(CartItem.cart_id == cart.cart_id)).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 2. Validate addresses
    shipping = session.get(Address, data.shipping_address_id)
    billing = session.get(Address, data.billing_address_id)

    if not shipping or shipping.user_id != user.user_id or shipping.deleted_at:
        raise HTTPException(status_code=400, detail="Invalid shipping address")

    if not billing or billing.user_id != user.user_id or billing.deleted_at:
        raise HTTPException(status_code=400, detail="Invalid billing address")

    if shipping.country != "US":
        raise HTTPException(status_code=400, detail="We currently ship only within the US")

    # 3. Validate stock BEFORE Stripe Checkout
    subtotal_cents = 0
    snapshot = []
    line_items = []

    # Older carts can hold the same product in several rows, so total them per product
    wanted = {}
    for item in cart_items:
        # A negative quantity would lower the total the customer pays
        if item.quantity < 1:
            raise HTTPException(status_code=400, detail="Invalid quantity in cart")
        wanted[item.product_id] = wanted.get(item.product_id, 0) + item.quantity

    for product_id, quantity in wanted.items():
        product = session.get(Product, product_id)

        if not product:
            raise HTTPException(status_code=400, detail="Product not found")

        if not product.is_active:
            raise HTTPException(status_code=400, detail=f"{product.title} is no longer available")

        if product.stock_quantity < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.title}"
            )

        unit_cents = to_cents(product.price)
        subtotal_cents += unit_cents * quantity
        snapshot.append([product_id, quantity, unit_cents])
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": unit_cents,
                "product_data": {"name": product.title, "tax_code": product_tax_code()},
                "tax_behavior": "exclusive",   # prices don't include tax; Stripe adds it
            },
            "quantity": quantity,
        })

    # What the customer pays for, so fulfillment doesn't depend on the cart later
    items_metadata = json.dumps(snapshot, separators=(",", ":"))
    if len(items_metadata) > 500:  # Stripe's limit for one metadata value
        raise HTTPException(status_code=400, detail="Too many different items for one checkout")

    shipping_amount = shipping_cents(subtotal_cents)
    shipping_option = {
        "shipping_rate_data": {
            "type": "fixed_amount",
            "display_name": "Free shipping" if shipping_amount == 0 else "Standard shipping",
            "fixed_amount": {"amount": shipping_amount, "currency": "usd"},
            "tax_behavior": "exclusive",
            "tax_code": SHIPPING_TAX_CODE,
        }
    }

    try:
        # Sales tax comes from Stripe Tax, using the customer's shipping address
        tax = {}
        if automatic_tax_enabled():
            tax = {"automatic_tax": {"enabled": True}, "customer": get_stripe_customer(session, user, shipping, billing)}

        # 4. Create Stripe Checkout Session
        # Payment methods (card, etc.) are configured in the Stripe Dashboard
        stripe_session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            shipping_options=[shipping_option],
            **tax,
            success_url=f"{frontend_url()}/order-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url()}/cart",
            metadata={
                "user_id": user.user_id,
                "shipping_address_id": data.shipping_address_id,
                "billing_address_id": data.billing_address_id,
                "items": items_metadata
            }
        )
    except stripe.StripeError as e:
        # Stripe is down, or the account isn't set up (e.g. Stripe Tax without a head
        # office address). The details are for us, not the shopper
        print("Failed to create checkout session:", e)
        raise HTTPException(status_code=502, detail="We couldn't start checkout. Please try again in a moment.")

    return {"checkoutUrl": stripe_session.url}


@router.get("/session/{session_id}")
def get_order_from_session(session_id: str, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.exec(
        select(Order).where(Order.stripe_session_id == session_id)
    ).first()

    # Webhook hasn't created the order yet (or never arrived): ask Stripe directly
    if not order:
        try:
            stripe_session = stripe.checkout.Session.retrieve(session_id)
        except Exception as e:
            print("Failed to load checkout session:", session_id, e)
            stripe_session = None

        owner_id = stripe_session.metadata.to_dict().get("user_id") if stripe_session and stripe_session.metadata else None
        if stripe_session and stripe_session.payment_status == "paid" and owner_id == str(user.user_id):
            order = fulfill_checkout(session, stripe_session)

    # Only the buyer (or an admin) can see the order; 404 so session ids can't be probed
    if not order or (order.user_id != user.user_id and not user.is_admin):
        raise HTTPException(status_code=404, detail="Order not found")

    return build_order_reads(session, [order])[0]

def summarize_payment_method(pmd: dict) -> dict:
    """Turn a charge's payment_method_details into how the customer paid.
    Checkout offers several methods (card, Link, Klarna, Cash App, ...), and only
    card-backed ones have a brand/last4."""
    method = pmd.get("type")
    details = pmd.get(method) or {}

    # Card, or a card funding another method (e.g. Amazon Pay)
    card = details if "last4" in details else (details.get("funding") or {}).get("card") or {}

    # Wallets (Apple Pay, Google Pay, Link) charge a card; show the wallet the customer picked
    wallet = (details.get("wallet") or {}).get("type") if method == "card" else None

    return {
        "payment_method_type": wallet or method,
        "card_brand": card.get("brand"),
        "card_last4": card.get("last4")
    }


def get_payment_details(payment_intent_id: str) -> dict:
    """Read payment + receipt details straight from Stripe, so the order doesn't
    depend on separate charge.* webhook events arriving in the right order."""
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id, expand=["latest_charge"])
        charge = intent.latest_charge
        if not charge:
            return {}

        pmd = charge.payment_method_details.to_dict() if charge.payment_method_details else {}

        return {
            **summarize_payment_method(pmd),
            "payment_status": charge.status,
            "receipt_url": charge.receipt_url
        }
    except Exception as e:
        print("Failed to load payment details for:", payment_intent_id, e)
        return {}


@router.post("/webhook")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # With an empty secret anyone could sign a fake event, so accept nothing
    if not WEBHOOK_SECRET:
        print("Webhook rejected: STRIPE_WEBHOOK_SECRET is not set")
        raise HTTPException(status_code=503, detail="Webhook is not configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        # Non-2xx so Stripe retries and the failure shows in the CLI/Dashboard
        print("Webhook signature failed:", e)
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        fulfill_checkout(session, event["data"]["object"])

    return {"received": True}


def fulfill_checkout(session: Session, stripe_session) -> Order | None:
    """Create the order for a completed Checkout Session. Called by the webhook and,
    as a fallback, by the success page, so it must be safe to run more than once."""

    metadata = stripe_session.metadata.to_dict() if stripe_session.metadata else {}

    # Sessions from `stripe trigger`, Payment Links, etc. don't carry our order metadata
    try:
        user_id = int(metadata["user_id"])
        shipping_id = int(metadata["shipping_address_id"])
        billing_id = int(metadata["billing_address_id"])
    except (KeyError, ValueError):
        print("Skipping checkout session without order metadata:", stripe_session.id)
        return None

    # Lock the user's cart so the webhook and the success page can't fulfill the same
    # session at once; the second caller waits here, then finds the committed order.
    cart = session.exec(select(Cart).where(Cart.user_id == user_id).with_for_update()).first()

    # Locking reads see rows committed by a concurrent fulfillment (plain reads may not)
    existing = session.exec(
        select(Order).where(Order.stripe_session_id == stripe_session.id).with_for_update()
    ).first()
    if existing:
        return existing

    user_obj = session.exec(select(User).where(User.user_id == user_id)).first()

    if not user_obj:
        print("ERROR: User not found: ", user_id)
        return None

    cart_items = []
    if cart:
        cart_items = session.exec(
            select(CartItem).where(CartItem.cart_id == cart.cart_id).with_for_update()
        ).all()

    # Fulfill what was paid for (snapshot taken at checkout), not whatever is in the cart now.
    # (product_id, quantity, unit price in cents)
    if "items" in metadata:
        purchased = [(int(pid), int(qty), int(cents)) for pid, qty, cents in json.loads(metadata["items"])]
    else:
        # Sessions created before the snapshot was added
        purchased = [(i.product_id, i.quantity, to_cents(session.get(Product, i.product_id).price)) for i in cart_items]

    if not purchased:
        return None

    # What Stripe charged. Sessions without these (older ones, `stripe trigger`) had
    # no shipping or tax, so the items are the whole amount
    charged = stripe_session.to_dict()
    totals = charged.get("total_details") or {}
    shipping_cents_paid = totals.get("amount_shipping") or 0
    tax_cents = totals.get("amount_tax") or 0
    subtotal_cents = charged.get("amount_subtotal")
    if subtotal_cents is None:
        subtotal_cents = sum(cents * qty for _, qty, cents in purchased)
    total_cents = charged.get("amount_total")
    if total_cents is None:
        total_cents = subtotal_cents + shipping_cents_paid + tax_cents

    pi_id = stripe_session.payment_intent

    order = Order(
        user_id=user_id,
        first_name=user_obj.first_name,
        last_name=user_obj.last_name,
        shipping_address_id=shipping_id,
        billing_address_id=billing_id,
        total_amount=from_cents(total_cents),
        subtotal_amount=from_cents(subtotal_cents),
        shipping_amount=from_cents(shipping_cents_paid),
        tax_amount=from_cents(tax_cents),
        order_number=str(uuid.uuid4())[:8],
        status="placed" if stripe_session.payment_status == "paid" else "pending",
        payment_intent_id=pi_id,
        stripe_session_id=stripe_session.id,
        # Saved addresses are only hidden when deleted, so these rows still exist
        shipping_address=address_snapshot(session.get(Address, shipping_id)),
        billing_address=address_snapshot(session.get(Address, billing_id)),
        **get_payment_details(pi_id)
    )

    session.add(order)
    session.flush()  # assigns order.order_id; everything below commits together

    for product_id, quantity, unit_cents in purchased:
        product = session.exec(select(Product).where(Product.product_id == product_id).with_for_update()).first()
        if not product:
            print("WARNING: purchased product no longer exists:", product_id, "order:", order.order_id)
            continue

        session.add(OrderItem(
            order_id=order.order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=from_cents(unit_cents),
            subtotal=from_cents(unit_cents * quantity)
        ))

        # Stock was checked at checkout, but another buyer may have taken it since
        if product.stock_quantity >= quantity:
            product.stock_quantity -= quantity
        else:
            print(f"OVERSOLD: product {product_id} had {product.stock_quantity}, order {order.order_id} needs {quantity}")
            product.stock_quantity = 0
        session.add(product)

    # Remove only what was bought; items added to the cart after checkout stay
    bought = {}
    for product_id, quantity, _ in purchased:
        bought[product_id] = bought.get(product_id, 0) + quantity

    for item in cart_items:
        remaining = item.quantity - bought.get(item.product_id, 0)
        if remaining > 0:
            item.quantity = remaining
            session.add(item)
        else:
            session.delete(item)

    session.commit()

    session.refresh(order)

    print("Created order:", order.order_id, "status:", order.status)

    return order
