from __future__ import annotations
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from datetime import datetime
from decimal import Decimal


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    order_id: int | None = Field(default = None, primary_key = True)
    # None for guest checkouts
    user_id: int | None = Field(default=None, foreign_key = "users.user_id")

    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    # Where order emails go: the account's email, or the one a guest gave Stripe
    email: str | None = Field(default=None)

    # Secret in the emailed tracking link, which opens the order without logging in
    access_token: str | None = Field(default=None, max_length=64, unique=True, index=True)


    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # The saved addresses used at checkout; None for guests, whose addresses Stripe collects
    shipping_address_id: int | None = Field(default=None, foreign_key="addresses.address_id")
    billing_address_id: int | None = Field(default=None, foreign_key="addresses.address_id")

    # Copies of the addresses when the order was placed (OrderAddress shape); the
    # saved addresses above can be edited or deleted afterwards
    shipping_address: dict | None = Field(default=None, sa_column=Column(JSON))
    billing_address: dict | None = Field(default=None, sa_column=Column(JSON))

    order_number: str = Field(index=True, unique=True)
    status: str = Field(default="pending")  # pending, paid, shipped, cancelled
    order_date: datetime = Field(default_factory=datetime.utcnow)
    # What the customer paid: total = subtotal (items) + shipping + tax. Orders from
    # before shipping and tax were charged have subtotal = total and 0 for both
    total_amount: Decimal = Field(max_digits=10, decimal_places=2)
    subtotal_amount: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    shipping_amount: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    tax_amount: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)

    # What has been refunded so far, from the admin's Refund button or Stripe's Dashboard.
    # refunded_at is when the order was refunded in full
    refunded_amount: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    refunded_at: datetime | None = Field(default=None)
    # When the order's items went back into stock (a full refund, a failed payment or
    # deleting an unpaid order), so they're never returned twice
    restocked_at: datetime | None = Field(default=None)

    payment_intent_id: str | None = Field(default=None, index=True)
    stripe_session_id: str | None = Field(default=None, unique=True, index=True)

    payment_method_type: str | None = Field(default=None)
    card_brand: str | None = Field(default=None)
    card_last4: str | None = Field(default=None)
    payment_status: str | None = Field(default=None)
    receipt_url: str | None = Field(default=None)

    tracking_number: str | None = Field(default=None)
    tracking_carrier: str | None = Field(default=None)
    tracking_url: str | None = Field(default=None)



class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    order_item_id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.order_id")
    product_id: int = Field(foreign_key="products.product_id")
    quantity: int
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    subtotal: Decimal = Field(max_digits=10, decimal_places=2)


    