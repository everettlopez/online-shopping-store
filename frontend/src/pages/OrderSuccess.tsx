import { useSearchParams, Link} from "react-router-dom";
import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";

export type Address = {
  address_id: number;
  user_id: number;
  line1: string;
  line2: string;
  city: string;
  state: string;
  postal_code: string;
  county: string;
  address_type: string;
};

export type OrderItem = {
  order_item_id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  subtotal: number;
  product: {
    product_id: number;
    name: string;
    price: number;
    size: string;
    image_url?: string;
  };
};

export type Order = {
  order_id: number;
  order_number: string;
  status: string;
  created_at: string;
  updated_at: string;
  order_date: string;
  total_amount: number;
  shipping_address: Address;
  billing_address: Address;

  payment_method_type: string | null;
  card_brand: string | null;
  card_last4: string | null;
  payment_status: string | null;
  receipt_url: string | null;

  items: OrderItem[];
};


export default function OrderSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");

  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);


  useEffect(() => {
    async function fetchOrder() {
      try {
        const res = await axiosClient.get(`/payments/session/${sessionId}`);

        const data = Array.isArray(res.data) ? res.data[0] : res.data;
        setOrder(data);
      } catch (err) {
        console.error("Failed to fetch order:", err);
      }
      setLoading(false);
    }

    if (sessionId) fetchOrder();
  }, [sessionId]);

  if (loading) return <p>Loading order...</p>;
  if (!order) return <p>Order not found.</p>;

  return (
    <>
    <div className="flex flex-col justify-center items-center min-h-screen min-w-screen p-5 bg-gray-100">

      <div className="border flex flex-col justify-center p-8 rounded-[10px] gap-8 w-[500px] bg-white">
        <h1 className="text-4xl tracking-wider text-center">THANK YOU FOR YOUR PURCHASE</h1>

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
            <p className="flex justify-center">{order.card_brand?.toUpperCase()}</p>
          </div>
        </div>

        {/* Billing Address */}
        <div className="flex flex-col">
          <p className="text-gray-400">Billing Address</p>
          <p>{order.billing_address.line1} {order.billing_address.city}, {order.billing_address.state} {order.billing_address.postal_code}</p>
        </div>

        {/* Order Items */}
        <div className="flex flex-col">
          {order.items.map(item => (
            <div key={item.order_item_id} className="border flex gap-2 p-3 justify-between rounded-[10px]">

              <div className="flex gap-2">
                <img src={item.product.image_url} className="h-20 w-20 object-cover"/>
                <div className="flex flex-col">
                  <p>{item.product.name}</p>
                  <p className="text-sm text-gray-500">Size: {item.product.size}</p>
                  <p className="text-sm text-gray-500">Quantity: {item.quantity}</p>
                </div>
              </div>

              <p>${item.product.price.toFixed(2)}</p>
            </div>
          ))}

        </div>

        <div className="flex flex-col py-4 gap-2">
          <div className="border"></div>

          <div className="flex justify-between p-3">
            <p>Total: </p>
            <p>${order.total_amount.toFixed(2)}</p>
          </div>

          <div className="border"></div>
        </div>

        <div className="flex justify-evenly">
          <a href={order.receipt_url || "#"} target="_blank" rel="noopener noreferrer" className="border py-2 px-5 rounded-[5px]">View Receipt</a>
          <Link to="/orders" className="border py-2 px-5 rounded-[5px]">Track Order</Link>
        </div>
      </div>

    </div>
    </>
  );
}
