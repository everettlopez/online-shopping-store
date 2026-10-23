from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
import stripe
import uuid
import json
import os
import secrets
from datetime import datetime

from app.db.session import get_session
from app.schemas.checkout import CheckoutRequest
from app.schemas.order import CheckoutOrderRead
from app.auth.core import OptionalUser
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
from app.schemas.address import OrderAddress, address_snapshot
from app.routes.order import build_order_reads
from app.models.user import User
from app.mail import build_order_confirmation_email, send_email

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


def stripe_address_snapshot(name: str | None, phone: str | None, address: dict | None) -> dict | None:
    """The OrderAddress copy of an address a guest entered on Stripe's page."""
    if not address or not address.get("line1"):
        return None
    return OrderAddress(
        full_name=name or "Customer",
        phone=phone,
        line1=address["line1"],
        line2=address.get("line2"),
        city=address.get("city") or "",
        state=address.get("state") or "",
        postal_code=address.get("postal_code") or "",
        country=address.get("country") or "US",
    ).model_dump()


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


def price_items(session: Session, items) -> tuple[list, list, int]:
    """Check what's being bought (positive quantities, active products, stock) and price
    it from the database. `items` are (product_id, quantity) pairs. Returns the
    [product_id, qty, unit_cents] snapshot, Stripe's line items and the subtotal in cents."""
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal_cents = 0
    snapshot = []
    line_items = []

    # Older carts can hold the same product in several rows, so total them per product
    wanted = {}
    for product_id, quantity in items:
        # A negative quantity would lower the total the customer pays
        if quantity < 1:
            raise HTTPException(status_code=400, detail="Invalid quantity in cart")
        wanted[product_id] = wanted.get(product_id, 0) + quantity

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

    return snapshot, line_items, subtotal_cents


@router.post("/create-checkout-session")
def create_checkout_session(data: CheckoutRequest, user: OptionalUser, session: Session = Depends(get_session)):
    if user:
        # 1. Logged in: the account cart, sent to their saved addresses
        cart = session.exec(select(Cart).where(Cart.user_id == user.user_id)).first()
        if not cart:
            raise HTTPException(status_code=400, detail="Cart not found")

        cart_items = session.exec(select(CartItem).where(CartItem.cart_id == cart.cart_id)).all()
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # 2. Validate addresses
        shipping = session.get(Address, data.shipping_address_id) if data.shipping_address_id else None
        billing = session.get(Address, data.billing_address_id) if data.billing_address_id else None

        if not shipping or shipping.user_id != user.user_id or shipping.deleted_at:
            raise HTTPException(status_code=400, detail="Invalid shipping address")

        if not billing or billing.user_id != user.user_id or billing.deleted_at:
            raise HTTPException(status_code=400, detail="Invalid billing address")

        if shipping.country != "US":
            raise HTTPException(status_code=400, detail="We currently ship only within the US")

        items = [(item.product_id, item.quantity) for item in cart_items]
    else:
        # 1. Guest: the browser cart. Stripe collects the email and addresses
        items = [(line.product_id, line.quantity) for line in data.items or []]

    # 3. Validate stock BEFORE Stripe Checkout
    snapshot, line_items, subtotal_cents = price_items(session, items)

    # What the customer pays for, so fulfillment doesn't depend on the cart later
    items_metadata = json.dumps(snapshot, separators=(",", ":"))
    if len(items_metadata) > 500:  # Stripe's limit for one metadata value
        raise HTTPException(status_code=400, detail="Too many different items for one checkout")

    if user:
        metadata = {
            "user_id": user.user_id,
            "shipping_address_id": data.shipping_address_id,
            "billing_address_id": data.billing_address_id,
            "items": items_metadata
        }
        # Addresses are already known; Stripe shows them from the customer
        collect = {}
    else:
        metadata = {"guest": "1", "items": items_metadata}
        collect = {
            "shipping_address_collection": {"allowed_countries": ["US"]},
            "billing_address_collection": "required",
            "phone_number_collection": {"enabled": True},   # carriers use it for delivery problems
        }

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
        # (a guest's is the one they enter on Stripe's page)
        tax = {}
        if automatic_tax_enabled():
            tax = {"automatic_tax": {"enabled": True}}
            if user:
                tax["customer"] = get_stripe_customer(session, user, shipping, billing)

        # 4. Create Stripe Checkout Session
        # Payment methods (card, etc.) are configured in the Stripe Dashboard
        stripe_session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            shipping_options=[shipping_option],
            **tax,
            **collect,
            success_url=f"{frontend_url()}/order-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url()}/cart",
            metadata=metadata
        )
    except stripe.StripeError as e:
        # Stripe is down, or the account isn't set up (e.g. Stripe Tax without a head
        # office address). The details are for us, not the shopper
        print("Failed to create checkout session:", e)
        raise HTTPException(status_code=502, detail="We couldn't start checkout. Please try again in a moment.")

    return {"checkoutUrl": stripe_session.url}


@router.get("/session/{session_id}", response_model=CheckoutOrderRead)
def get_order_from_session(session_id: str, user: OptionalUser, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
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

        metadata = stripe_session.metadata.to_dict() if stripe_session and stripe_session.metadata else {}
        is_buyer = metadata.get("guest") == "1" or (user is not None and metadata.get("user_id") == str(user.user_id))
        if stripe_session and stripe_session.payment_status == "paid" and is_buyer:
            order = fulfill_checkout(session, stripe_session, background_tasks)

    # A guest order is shown to whoever has its Checkout Session id, a long random
    # secret that Stripe hands only to the buyer's browser. An account's order is shown
    # only to its owner (or an admin); 404 so session ids can't be probed
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id is not None and (user is None or (order.user_id != user.user_id and not user.is_admin)):
        raise HTTPException(status_code=404, detail="Order not found")

    read = build_order_reads(session, [order])[0]
    return CheckoutOrderRead(**read.model_dump(), access_token=order.access_token)

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
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
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
        fulfill_checkout(session, event["data"]["object"], background_tasks)

    return {"received": True}


def already_fulfilled(session: Session, stripe_session_id: str) -> Order | None:
    """A concurrent fulfillment of the same session committed its order first (guests
    have no cart row to wait on). Drop ours, including its stock changes, and use that one."""
    session.rollback()
    return session.exec(select(Order).where(Order.stripe_session_id == stripe_session_id)).first()


def fulfill_checkout(session: Session, stripe_session, background_tasks: BackgroundTasks) -> Order | None:
    """Create the order for a completed Checkout Session. Called by the webhook and,
    as a fallback, by the success page, so it must be safe to run more than once.
    The confirmation email goes out only when this call creates the order."""

    metadata = stripe_session.metadata.to_dict() if stripe_session.metadata else {}

    # Sessions from `stripe trigger`, Payment Links, etc. don't carry our order metadata
    guest = metadata.get("guest") == "1"
    if guest:
        user_id = shipping_id = billing_id = None
    else:
        try:
            user_id = int(metadata["user_id"])
            shipping_id = int(metadata["shipping_address_id"])
            billing_id = int(metadata["billing_address_id"])
        except (KeyError, ValueError):
            print("Skipping checkout session without order metadata:", stripe_session.id)
            return None

    # Lock the user's cart so the webhook and the success page can't fulfill the same
    # session at once; the second caller waits here, then finds the committed order.
    # Guests have no cart to lock: the unique stripe_session_id catches them below
    cart = None
    if not guest:
        cart = session.exec(select(Cart).where(Cart.user_id == user_id).with_for_update()).first()

    # Locking reads see rows committed by a concurrent fulfillment (plain reads may not)
    existing = session.exec(
        select(Order).where(Order.stripe_session_id == stripe_session.id).with_for_update()
    ).first()
    if existing:
        return existing

    charged = stripe_session.to_dict()

    if guest:
        # Who the guest is and where it goes, as entered on Stripe's page
        details = charged.get("customer_details") or {}
        # Newer Stripe API versions keep the shipping details under collected_information
        shipping_details = (charged.get("collected_information") or {}).get("shipping_details") or charged.get("shipping_details") or {}
        email = details.get("email")
        shipping_address = stripe_address_snapshot(shipping_details.get("name") or details.get("name"), details.get("phone"), shipping_details.get("address"))
        billing_address = stripe_address_snapshot(details.get("name") or shipping_details.get("name"), details.get("phone"), details.get("address"))
        first_name, _, last_name = ((shipping_address or billing_address or {}).get("full_name") or "").partition(" ")
    else:
        user_obj = session.exec(select(User).where(User.user_id == user_id)).first()

        if not user_obj:
            print("ERROR: User not found: ", user_id)
            return None

        email = user_obj.email
        first_name, last_name = user_obj.first_name, user_obj.last_name
        # Saved addresses are only hidden when deleted, so these rows still exist
        shipping_address = address_snapshot(session.get(Address, shipping_id))
        billing_address = address_snapshot(session.get(Address, billing_id))

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
        first_name=first_name or None,
        last_name=last_name or None,
        email=email,
        access_token=secrets.token_urlsafe(32),
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
        shipping_address=shipping_address,
        billing_address=billing_address,
        **get_payment_details(pi_id)
    )

    session.add(order)
    try:
        session.flush()  # assigns order.order_id; everything below commits together
    except IntegrityError:
        return already_fulfilled(session, stripe_session.id)

    email_items = []  # (title, quantity, unit price, subtotal) for the confirmation email

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
        email_items.append((product.title, quantity, from_cents(unit_cents), from_cents(unit_cents * quantity)))

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

    try:
        session.commit()
    except IntegrityError:
        return already_fulfilled(session, stripe_session.id)

    session.refresh(order)

    print("Created order:", order.order_id, "status:", order.status)

    # Sent after the response, so neither Stripe nor the shopper waits on the email
    # provider. Unpaid (pending) orders get no confirmation
    if order.status == "placed" and order.email:
        background_tasks.add_task(send_email, build_order_confirmation_email(order.email, order, email_items))

    return order
