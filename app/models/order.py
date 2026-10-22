from __future__ import annotations
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from datetime import datetime
from decimal import Decimal
from typing import Optional


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    order_id: int | None = Field(default = None, primary_key = True)
    user_id: int = Field(foreign_key = "users.user_id")

    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)


    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    shipping_address_id: int = Field(foreign_key="addresses.address_id")
    billing_address_id: int = Field(foreign_key="addresses.address_id")

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

    payment_intent_id: str | None = Field(default=None, index=True)
    stripe_session_id: str | None = Field(default=None, index=True)

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


    