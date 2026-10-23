import { useSearchParams, Link} from "react-router-dom";
import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";
import { paymentCardSummary, paymentMethodLabel } from "../utils/payment";
import OrderAddressLines, { type OrderAddress } from "../components/OrderAddressLines";
import OrderTotals from "../components/OrderTotals";
import Navbar from "../components/Navbar";
import { removePurchasedFromGuestCart, useCart } from "../context/CartContext";

export type OrderItem = {
  order_item_id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  subtotal: number;
  // null when the product has since been removed from the catalog
  product: {
    product_id: number;
    title: string;
    price: number;
    size: string | null;
    thumbnail: string | null;
    images?: string[] | null;
  } | null;
};

export type Order = {
  order_id: number;
  order_number: string;
  status: string;
  created_at: string;
  updated_at: string;
  order_date: string;
  total_amount: number;
  subtotal_amount: number | null;
  shipping_amount: number | null;
  tax_amount: number | null;
  shipping_address: OrderAddress | null;
  billing_address: OrderAddress | null;

  // None for guest orders
  user_id?: number | null;
  email?: string | null;

  payment_method_type: string | null;
  card_brand: string | null;
  card_last4: string | null;
  payment_status: string | null;
  receipt_url: string | null;

  items: OrderItem[];
};

// The checkout success page also gets the secret for the order's tracking link
type CheckoutOrder = Order & { access_token: string | null };

// True if this order's items were already taken out of the browser cart; marks it if not
function alreadyClearedFor(orderNumber: string): boolean {
  const key = `cart_cleared_${orderNumber}`;
  try {
    if (localStorage.getItem(key)) return true;
    localStorage.setItem(key, "1");
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
      } catch (err: any) {
        // Stripe's webhook can land a moment after the redirect, so retry while the order is created
        if (err.response?.status === 404 && attempt < 5) {
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

  if (loading) return <p>Loading order...</p>;
  if (!order) return <p>Order not found.</p>;

  // Account orders are in the order history; guests use the private tracking link
  const trackLink = order.user_id != null
    ? `/orders/${order.order_number}`
    : `/track/${encodeURIComponent(order.order_number)}?token=${encodeURIComponent(order.access_token ?? "")}`;

  return (
    <>
    <Navbar />
    <div className="flex flex-col justify-center items-center min-h-screen min-w-screen p-5 bg-gray-100">

      <div className="border flex flex-col justify-center p-8 rounded-[10px] gap-8 w-[500px] bg-white">
        <h1 className="text-4xl tracking-wider text-center">THANK YOU FOR YOUR PURCHASE</h1>
        {order.email && (
          <p className="text-center text-gray-500">A confirmation with a link to track your order is on its way to {order.email}.</p>
        )}

        {/* Order Information */}
        <div className="flex justify-between">

          <div className="flex flex-col">
            <p className="text-gray-400">Date</p>
            <p className="flex justify-center">
              {new Date(order.order_date).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>

          </div>

          <div className="flex flex-col">
            <p className="text-gray-400">Order Number</p>
            <p className="flex justify-center">{order.order_number}</p>
          </div>
          
          <div className="flex flex-col">
            <p className="text-gray-400">Payment Method</p>
            <p className="flex justify-center">{paymentMethodLabel(order.payment_method_type)}</p>
            {paymentCardSummary(order) && <p className="flex justify-center">{paymentCardSummary(order)}</p>}
          </div>
        </div>

        {/* Billing Address */}
        <div className="flex flex-col">
          <p className="text-gray-400">Billing Address</p>
          <OrderAddressLines address={order.billing_address} />
        </div>

        {/* Order Items */}
        <div className="flex flex-col">
          {order.items.map(item => (
            <div key={item.order_item_id} className="border flex gap-2 p-3 justify-between rounded-[10px]">

              <div className="flex gap-2">
                {item.product?.thumbnail || item.product?.images?.[0]
                  ? <img src={item.product.thumbnail || item.product.images?.[0]} className="h-20 w-20 object-cover"/>
                  : <div className="h-20 w-20 bg-gray-100"/>}
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

        <div className="flex justify-evenly">
          <a href={order.receipt_url || "#"} target="_blank" rel="noopener noreferrer" className="border py-2 px-5 rounded-[5px]">View Receipt</a>
          <Link to={trackLink} className="border py-2 px-5 rounded-[5px]">Track Order</Link>
        </div>
      </div>

    </div>
    </>
  );
}
