import { useSearchParams, Link} from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import axiosClient from "../api/axiosClient";
import { paymentCardSummary, paymentMethodLabel } from "../utils/payment";
import OrderAddressLines from "../components/OrderAddressLines";
import OrderTotals from "../components/OrderTotals";
import Navbar from "../components/Navbar";
import { EmptyState, LoadingState } from "../components/Status";
import type { Order } from "../components/orders/OrderView";
import { useCart } from "../context/useCart";
import { removePurchasedFromGuestCart } from "../context/guestCart";

// The checkout success page also gets the secret for the order's tracking link
type CheckoutOrder = Order & { access_token: string | null };

// Guest orders whose items were already taken out of the browser cart (the latest few)
const CLEARED_ORDERS_KEY = "guest_cart_cleared_orders";

// True if this order's items were already taken out of the browser cart; marks it if not
function alreadyClearedFor(orderNumber: string): boolean {
  try {
    const cleared: unknown = JSON.parse(localStorage.getItem(CLEARED_ORDERS_KEY) ?? "[]");
    const orders = Array.isArray(cleared) ? cleared : [];
    if (orders.includes(orderNumber)) return true;
    localStorage.setItem(CLEARED_ORDERS_KEY, JSON.stringify([...orders, orderNumber].slice(-20)));
  } catch {
    // Storage blocked: the browser cart isn't saved either, so there's nothing to repeat
  }
  return false;
}


export default function OrderSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");

  const [order, setOrder] = useState<CheckoutOrder | null>(null);
  const { reload: reloadCart } = useCart();
  const [loading, setLoading] = useState(Boolean(sessionId));


  useEffect(() => {
    let cancelled = false;

    async function fetchOrder(attempt: number) {
      try {
        const res = await axiosClient.get(`/payments/session/${sessionId}`);

        const data: CheckoutOrder = Array.isArray(res.data) ? res.data[0] : res.data;
        if (cancelled) return;
        setOrder(data);
        // What was bought is no longer in the cart (the server already updated an account
        // cart). Only once per order, so revisiting this page keeps items added since
        if (data.user_id == null && !alreadyClearedFor(data.order_number)) {
          removePurchasedFromGuestCart(data.items.map((item) => ({ product_id: item.product?.product_id ?? item.product_id, quantity: item.quantity })));
        }
        reloadCart();
      } catch (err) {
        // Stripe's webhook can land a moment after the redirect, so retry while the order is created
        if (axios.isAxiosError(err) && err.response?.status === 404 && attempt < 5) {
          setTimeout(() => { if (!cancelled) fetchOrder(attempt + 1); }, 1000);
          return;
        }
        console.error("Failed to fetch order:", err);
      }
      if (!cancelled) setLoading(false);
    }

    if (sessionId) fetchOrder(1);

    return () => { cancelled = true; };
  }, [sessionId, reloadCart]);

  if (loading) return <><Navbar /><LoadingState label="Confirming your order" page /></>;
  if (!order) {
    return (
      <>
      <Navbar />
      <EmptyState
        title="We couldn't find this order"
        message="If you were charged, a confirmation email is on its way. You can also look the order up with its number and your email."
        action={{ to: "/track", label: "Find my order" }}
      />
      </>
    );
  }

  // Account orders are in the order history; guests use the private tracking link
  const trackLink = order.user_id != null
    ? `/orders/${order.order_number}`
    : `/track/${encodeURIComponent(order.order_number)}?token=${encodeURIComponent(order.access_token ?? "")}`;

  return (
    <>
    <Navbar />
    <main>
    <div className="flex flex-col justify-center items-center min-h-screen p-3 sm:p-5 bg-gray-100">

      <div className="border flex flex-col justify-center p-5 sm:p-8 rounded-[10px] gap-8 w-full max-w-[500px] bg-white">
        <h1 className="text-3xl sm:text-4xl tracking-wider text-center">THANK YOU FOR YOUR PURCHASE</h1>
        {order.email && (
          <p className="text-center text-gray-500">A confirmation with a link to track your order is on its way to {order.email}.</p>
        )}

        {/* Order Information */}
        <div className="flex flex-wrap justify-between gap-4">

          <div className="flex flex-col">
            <p className="text-gray-500">Date</p>
            <p className="flex justify-center">
              {new Date(order.order_date).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>

          </div>

          <div className="flex flex-col">
            <p className="text-gray-500">Order Number</p>
            <p className="flex justify-center break-all">{order.order_number}</p>
          </div>
          
          <div className="flex flex-col">
            <p className="text-gray-500">Payment Method</p>
            <p className="flex justify-center">{paymentMethodLabel(order.payment_method_type)}</p>
            {paymentCardSummary(order) && <p className="flex justify-center">{paymentCardSummary(order)}</p>}
          </div>
        </div>

        {/* Billing Address */}
        <div className="flex flex-col">
          <p className="text-gray-500">Billing Address</p>
          <OrderAddressLines address={order.billing_address} />
        </div>

        {/* Order Items */}
        <div className="flex flex-col">
          {order.items.map(item => (
            <div key={item.order_item_id} className="border flex gap-2 p-3 justify-between rounded-[10px]">

              <div className="flex gap-2 min-w-0">
                {item.product?.thumbnail || item.product?.images?.[0]
                  ? <img src={item.product.thumbnail || item.product.images?.[0]} alt={item.product.title} className="h-20 w-20 object-cover shrink-0"/>
                  : <div className="h-20 w-20 bg-gray-100 shrink-0"/>}
                <div className="flex flex-col">
                  <p>{item.product?.title ?? "Product no longer available"}</p>
                  {item.product?.size && <p className="text-sm text-gray-500">Size: {item.product.size}</p>}
                  <p className="text-sm text-gray-500">Quantity: {item.quantity}</p>
                </div>
              </div>

              {/* The price paid, not the product's current price */}
              <p>${item.unit_price.toFixed(2)}</p>
            </div>
          ))}

        </div>

        <div className="flex flex-col py-4 gap-2">
          <div className="border"></div>

          <div className="p-3">
            <OrderTotals order={order} />
          </div>

          <div className="border"></div>
        </div>

        <div className="flex flex-wrap justify-evenly gap-3">
          <a href={order.receipt_url || "#"} target="_blank" rel="noopener noreferrer" className="border py-2 px-5 rounded-[5px]">View Receipt</a>
          <Link to={trackLink} className="border py-2 px-5 rounded-[5px]">Track Order</Link>
        </div>
      </div>

    </div>
    </main>
    </>
  );
}
