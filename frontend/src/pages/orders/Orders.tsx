import { Link } from "react-router-dom";
import axiosClient from "../../api/axiosClient";
import { paymentCardSummary, paymentMethodLabel } from "../../utils/payment";
import { useEffect, useState } from "react";
import type { ReactElement } from "react";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { Chip } from "@mui/material";

import AttachMoneyRoundedIcon from '@mui/icons-material/AttachMoneyRounded';
import SettingsRoundedIcon from '@mui/icons-material/SettingsRounded';
import LocalShippingRoundedIcon from '@mui/icons-material/LocalShippingRounded';
import DoneRoundedIcon from '@mui/icons-material/DoneRounded';
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import NotInterestedRoundedIcon from '@mui/icons-material/NotInterestedRounded';

import Navbar from "../../components/Navbar";
import OrderAddressLines, { type OrderAddress } from "../../components/OrderAddressLines";
import AccountNav from "../../components/AccountNav";
import { OrderStepper } from "../../components/orders/OrderView";
import { EmptyState, ErrorState, LoadingState } from "../../components/Status";

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
  user_id: number;

  first_name: string | null;
  last_name: string | null;

  created_at: string;
  updated_at: string;

  shipping_address_id: number;
  billing_address_id: number;

  order_number: string;
  status: string;
  order_date: string;
  total_amount: number;
  subtotal_amount: number | null;
  shipping_amount: number | null;
  tax_amount: number | null;

  payment_intent_id: string | null;
  stripe_session_id: string | null;

  payment_method_type: string | null;
  card_brand: string | null;
  card_last4: string | null;
  payment_status: string | null;
  receipt_url: string | null;

  shipping_address: OrderAddress | null;
  billing_address: OrderAddress | null;

  tracking_number: string | null,
  tracking_carrier: string | null,
  tracking_url: string | null,

  items: OrderItem[];
};

type StatusColor =
  | "info"
  | "success"
  | "error"
  | "warning"
  | "default"
  | "primary"
  | "secondary";

const getStatusChipProps = (status: string): {
    color: StatusColor;
    icon: ReactElement | undefined;
    label: string;
  } => {
    const s = status.toLowerCase();

    switch (s) {
      case "placed":
        return {
          color: "default",
          icon: <AttachMoneyRoundedIcon />,
          label: "PLACED"
        };

      case "processing":
        return {
          color: "default",
          icon: <SettingsRoundedIcon />,
          label: "PROCESSING"
        };

      case "shipped":
        return {
          color: "default",
          icon: <LocalShippingRoundedIcon />,
          label: "SHIPPED"
        };

      case "delivered":
        return {
          color: "success",
          icon: <DoneRoundedIcon />,
          label: "DELIVERED"
        };

      case "completed":
        return {
          color: "success",
          icon: <DoneAllRoundedIcon />,
          label: "COMPLETED"
        };

      case "cancelled":
        return {
          color: "error",
          icon: <NotInterestedRoundedIcon />,
          label: "CANCELLED"
        };

      case "refunded":
        return {
          color: "warning",
          icon: <ErrorOutlineRoundedIcon />,
          label: "REFUNDED"
        };

      default:
        return {
          color: "default",
          icon: <LocalShippingRoundedIcon />,   // IMPORTANT: not null
          label: status.toUpperCase()
        };
    }
  };

const FINISHED = ["cancelled", "completed", "refunded", "delivered"];

const formatDate = (date: string) =>
    new Date(date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });

// One order in the list. Current orders also show their progress and tracking
function OrderSummary({ order, current }: { order: Order; current: boolean }) {
    const chipProps = getStatusChipProps(order.status);
    const safeUrl = order.tracking_url?.startsWith("http://") || order.tracking_url?.startsWith("https://") ? order.tracking_url : `https://${order.tracking_url}`;

    return (
        <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <div className="flex flex-col min-w-0">
                    <p className="text-gray-500">{formatDate(order.order_date)}</p>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 items-center">
                        <p className="text-lg break-all">ORDER: #{order.order_number.toUpperCase()}</p>
                        <Chip size="small" color={chipProps.color} icon={chipProps.icon} label={chipProps.label} />
                    </div>
                </div>
            </AccordionSummary>

            <AccordionDetails>
                {current && <OrderStepper status={order.status} />}

                {/* Two columns on phones, four in a row from 768 px */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4 md:divide-x [&>div]:md:px-4">
                    <div className="flex flex-col">
                        <p className="text-sm text-gray-500">Placed By</p>
                        <p className="text-lg">{order.first_name} {order.last_name}</p>
                        <p>{formatDate(order.order_date)}</p>
                    </div>

                    <div className="flex flex-col">
                        <p className="text-sm text-gray-500">Shipping</p>
                        <OrderAddressLines address={order.shipping_address} />
                    </div>

                    <div className="flex flex-col">
                        <p className="text-sm text-gray-500">Billing</p>
                        <OrderAddressLines address={order.billing_address} />
                    </div>

                    <div className="flex flex-col">
                        <p className="text-sm text-gray-500">Payment</p>
                        <p>${order.total_amount.toFixed(2)} with {paymentMethodLabel(order.payment_method_type)}</p>
                        {paymentCardSummary(order) && <p>{paymentCardSummary(order)}</p>}
                    </div>
                </div>

                {order.status === "shipped" && (
                    <div className="flex flex-col">
                        <p className="text-lg tracking-wider">TRACKING INFORMATION</p>
                        <div className="flex flex-col px-4 py-1">
                            <p className="tracking-wider">Tracking #: {order.tracking_number?.toUpperCase()}</p>
                            <p className="tracking-wider">Shipping Carrier: {order.tracking_carrier?.toUpperCase()}</p>
                            <div className="flex flex-wrap gap-x-2 items-center">
                                <p className="tracking-wider">Tracking URL:</p>
                                <a href={safeUrl} className="text-gray-600 underline break-all">{order.tracking_url}</a>
                            </div>
                        </div>
                    </div>
                )}

                <div className="p-4 flex justify-end">
                    <Link to={`/orders/${order.order_number}`} className="border px-5 py-2 rounded-full">
                        {current ? "View Order" : "Track Order"}
                    </Link>
                </div>
            </AccordionDetails>
        </Accordion>
    );
}

export default function Orders()
{
    const [orders, setOrders] = useState<Order[] | null>(null);
    const [failed, setFailed] = useState(false);
    // Bumped by "Try again" to load the orders once more
    const [attempt, setAttempt] = useState(0);

    useEffect(() => {
        let cancelled = false;

        axiosClient.get<Order[]>("/orders/me")
            .then((response) => { if (!cancelled) setOrders(response.data); })
            .catch((err) => {
                console.error("Failed to load orders", err);
                if (!cancelled) setFailed(true);
            });

        return () => { cancelled = true; };
    }, [attempt]);

    function retry() {
        setFailed(false);
        setAttempt((n) => n + 1);
    }

    const pendingOrders = orders?.filter((order) => !FINISHED.includes(order.status)) ?? [];
    const orderHistory = orders?.filter((order) => FINISHED.includes(order.status)) ?? [];

    return (
        <>
        {/* Header */}
        <Navbar />
        <main>

        <div className="flex flex-col md:flex-row gap-6 px-4 py-6 md:p-8">

            <AccountNav />

            {/* Orders */}
            <div className="bg-gray-100 flex-1 min-w-0 flex flex-col p-3 sm:p-8 gap-6 rounded-[10px]">
                {failed ? (
                    <ErrorState message="We couldn't load your orders." onRetry={retry} />
                ) : orders === null ? (
                    <LoadingState label="Loading orders" />
                ) : orders.length === 0 ? (
                    <EmptyState
                        title="No orders yet"
                        message="When you place an order, you can follow it here."
                        action={{ to: "/products", label: "Start shopping" }}
                    />
                ) : (
                    <>
                    <section className="flex flex-col gap-4">
                        <h2 className="text-2xl sm:text-3xl tracking-wider">CURRENT ORDERS</h2>
                        {pendingOrders.length === 0 ? (
                            <p className="border py-4 px-4 rounded-[10px] text-center text-gray-500 bg-white">No orders on their way right now.</p>
                        ) : (
                            pendingOrders.map((order) => <OrderSummary key={order.order_id} order={order} current />)
                        )}
                    </section>

                    <section className="flex flex-col gap-4">
                        <h2 className="text-2xl sm:text-3xl tracking-wider">ORDER HISTORY</h2>
                        {orderHistory.length === 0 ? (
                            <p className="border py-4 px-4 rounded-[10px] text-center text-gray-500 bg-white">No past orders yet.</p>
                        ) : (
                            orderHistory.map((order) => <OrderSummary key={order.order_id} order={order} current={false} />)
                        )}
                    </section>
                    </>
                )}
            </div>

        </div>
        </main>
        </>
    );
}
