import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import axiosClient from "../../api/axiosClient";
import { useEffect, useState } from "react";
import type { ReactElement } from "react";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { Chip, FormControl, InputLabel, MenuItem, Select, Step, StepLabel } from "@mui/material";

import Box from '@mui/material/Box';
import AttachMoneyRoundedIcon from '@mui/icons-material/AttachMoneyRounded';
import SettingsRoundedIcon from '@mui/icons-material/SettingsRounded';
import LocalShippingRoundedIcon from '@mui/icons-material/LocalShippingRounded';
import DoneRoundedIcon from '@mui/icons-material/DoneRounded';
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import NotInterestedRoundedIcon from '@mui/icons-material/NotInterestedRounded';
import TextField from '@mui/material/TextField';

import Stepper from '@mui/material/Stepper';

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

  payment_intent_id: string | null;
  stripe_session_id: string | null;

  payment_method_type: string | null;
  card_brand: string | null;
  card_last4: string | null;
  payment_status: string | null;
  receipt_url: string | null;

  shipping_address: Address;
  billing_address: Address;

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

type OrderStatus = "placed" | "processing" | "shipped" | "delivered";

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

export default function Orders()
{
    const [orderHistory, setOrderHistory] = useState<Order[]>([]);
    const [pendingOrders, setPendingOrders] = useState<Order[]>([]);

    const { user } = useAuth();

    const [orders, setOrders] = useState<Order[]>([]);
    const [currentOrder, setCurrentOrder] = useState<Order | null>(null);

    const steps = ["Placed", "Processing", "Shipped", "Delivered"];
    const stepIndexMap: Record<OrderStatus, number> = { placed: 0, processing: 1, shipped: 2, delivered: 3 };

    useEffect(() => {
        async function fetchOrders() {
            try
            {
                const response = await axiosClient.get("/orders/me");
                const data: Order[] = response.data;

                const active = data.filter(order => !["cancelled", "completed", "refunded", "delivered"].includes(order.status));
                const history = data.filter(order => ["cancelled", "completed", "refunded", "delivered"].includes(order.status));

                setPendingOrders(active);
                setOrderHistory(history);
                setCurrentOrder(active[0] || null);

                setOrders(data);

            }
            catch (err)
            {
                console.error("Failed to load orders", err);
            }
        }

        fetchOrders();
    }, []);

    function OrderStepper({order}: {order: Order}) {
        const activeStep = stepIndexMap[order.status as OrderStatus];
    
        return (
          <div className="p-8">
            <Stepper activeStep={activeStep} alternativeLabel>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel className="flex flex-col">{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
          </div>
        );
      }

    return (
        <>
        {/* Header */}
        <div className="flex flex-col justify-center items-center gap-4 p-5">

            {/* Right-side icons */}
            <div className="absolute right-5 top-5 flex items-center gap-6 text-2xl">
                <Link to="/account" className="hover:text-gray-600 transition">
                    <i className="fa-regular fa-user"></i>
                </Link>

                <Link to="/cart" className="hover:text-gray-600 transition">
                    <i className="fa-solid fa-bag-shopping"></i>
                </Link>
            </div>

            <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

            <nav className="flex gap-12">
                <Link to="/"><p className="text-base font-normal tracking-widest">EVENTS</p></Link>
                <Link to="/products?category=1"><p className="text-base font-normal tracking-widest">NEW ARRIVALS</p></Link>
                <Link to="/products?category=2"><p className="text-base font-normal tracking-widest">WOMEN</p></Link>
                <Link to="/products?category=3"><p className="text-base font-normal tracking-widest">MEN</p></Link>
                <Link to="/products?category=4"><p className="text-base font-normal tracking-widest">BRANDS</p></Link>
                <Link to="/products?category=5"><p className="text-base font-normal tracking-widest">ACCESSORIES</p></Link>
                <Link to="/products?category=6"><p className="text-base font-normal tracking-widest">JEWELERY</p></Link>
            </nav>
        </div>

        <div className="flex gap-2 p-8">

            {/* Account / User Navigation */}
            <div className="flex flex-col h-full p-10 gap-4">

                <div className="flex flex-col items-end">
                    <Link to="/account" className="text-xl tracking-widest">ACCOUNT</Link>
                    <Link to="/" className="tracking-wider">SETTINGS</Link>
                    {user?.is_admin === true ? (
                        <Link to="/admin">ADMIN</Link>
                    ) : (
                        <div>
                        </div>
                    )}
                </div>

                <div className="flex flex-col items-end">
                    <Link to="/orders" className="text-xl tracking-widest">ORDERS</Link>
                    <Link to="" className="tracking-wider">TRACK</Link>
                    <Link to="" className="tracking-wider">HISTORY</Link>
                </div>

            </div>

            {/* Orders */}
            <div className="bg-gray-100 h-full w-screen flex flex-col p-8 gap-3">

                <div className="flex flex-col gap-4">
                    <p className="text-3xl tracking-wider">CURRENT ORDERS</p>
                    {/* No Pending Orders */}
                    {pendingOrders.length === 0 && (
                        <>
                        <div className="border py-4 rounded-[10px] flex justify-center items-center mx-auto w-full">
                            <p className="text-gray-500">No pending orders. Try shopping around.</p>
                        </div>
                        </>
                    )}

                    {/* Current (Pending) Order */}
                    {pendingOrders.map((order) => {
                        const chipProps = getStatusChipProps(order.status);
                        const safeUrl = order.tracking_url?.startsWith("http://") || order.tracking_url?.startsWith("https://") ? order.tracking_url : `https://${order.tracking_url}`; 
                        return(
                            <>
                            <div className="flex flex-col gap-3" key={order.order_id}>
                                <Accordion>
                                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                        <div className="flex flex-col">
                                            <p className="text-gray-400">
                                                {new Date(order.order_date).toLocaleDateString("en-US", {
                                                    month: "long",
                                                    day: "numeric",
                                                    year: "numeric",
                                                })}
                                                </p>
                                            
                                            <div className="flex gap-4 items-center">
                                                <p className="text-lg">ORDER: #{order.order_number.toUpperCase()}</p>
                                                <Chip size="small" color={chipProps.color} icon={chipProps.icon} label={chipProps.label} />
                                            </div>
                                        </div>
                                    </AccordionSummary>

                                    <AccordionDetails>
                                        {order.status !== "completed" && (
                                            <OrderStepper order={order}/>
                                        )}

                                        <div className="flex gap-2 justify-evenly py-6">
                                            <div className="flex flex-col">
                                                <p className="text-sm text-gray-400">Placed By</p>
                                                <p className="text-lg">{order.first_name} {order.last_name}</p>
                                                <p>
                                                {new Date(order.order_date).toLocaleDateString("en-US", {
                                                    month: "long",
                                                    day: "numeric",
                                                    year: "numeric",
                                                })}
                                                </p>

                                            </div>

                                            <div className="border"/>

                                            <div className="flex flex-col">
                                                <p className="text-sm text-gray-400">Shipping</p>
                                                <p>{order.shipping_address.line1}</p>
                                                <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}</p>
                                            </div>

                                            <div className="border"/>

                                            <div className="flex flex-col">
                                                <p className="text-sm text-gray-400">Billing</p>
                                                <p>{order.billing_address.line1}</p>
                                                <p>{order.billing_address.city}, {order.billing_address.state} {order.billing_address.postal_code}</p>
                                            </div>

                                            <div className="border"/>

                                            <div className="flex flex-col">
                                                <p className="text-sm text-gray-400">Payment</p>
                                                <p>
                                                ${order.total_amount.toFixed(2)} with {order?.payment_method_type
                                                    ? order.payment_method_type.charAt(0).toUpperCase() +
                                                    order.payment_method_type.slice(1)
                                                    : ""}
                                                </p>
                                                <p>{order.card_brand?.toUpperCase()} ending in ****{order.card_last4}</p>

                                            </div>
                                        </div>

                                        {order.status !== "placed" && order.status !=="processing" && (
                                            <div className="flex flex-col">
                                                <p className="text-lg tracking-wider">TRACKING INFORMATION</p>
                                                <div className="flex flex-col px-4 py-1">
                                                    <p className="tracking-wider">Tracking #: {order.tracking_number?.toUpperCase()}</p>
                                                    <p className="tracking-wider">Shipping Carrier: {order.tracking_carrier?.toUpperCase()}</p>
                                                    <div className="flex gap-2 items-center">
                                                        <p className="tracking-wider">Tracking URL:</p>
                                                        <a href={safeUrl} className="text-gray-400">{order.tracking_url}</a>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        <div className="p-4 flex justify-end">
                                            <Link to={order ? `/orders/${order.order_number}` : "#"} className="border px-5 py-2 rounded-full">View Order</Link>
                                        </div>
                                    </AccordionDetails>
                                </Accordion>
                                
                            </div>
                            </>
                        );
                    }
                    )}
                </div>

                <div className="flex flex-col gap-4">
                    <p className="text-3xl tracking-wider">ORDER HISTORY</p>

                    {orderHistory.length === 0 && (
                        <>
                        <div className="border py-4 rounded-[10px] flex justify-center items-center mx-auto w-full">
                            <p className="text-gray-500">No order history</p>
                        </div>
                        </>
                    )}

                    {/* Completed, Cancelled, or Refunded Orders (Not working on) */}
                    {orderHistory.map((order: Order) => {
                        const chipProps = getStatusChipProps(order.status);
                        return (
                            <>
                            <div className="flex flex-col gap-3">
                                <Accordion>
                                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                        <div className="flex flex-col">
                                            <p className="text-gray-400">
                                                {new Date(order.order_date).toLocaleDateString("en-US", {
                                                    month: "long",
                                                    day: "numeric",
                                                    year: "numeric",
                                                })}
                                                </p>
                                            
                                            <div className="flex gap-4 items-center">
                                                <p className="text-lg">ORDER: #{order.order_number.toUpperCase()}</p>
                                                <Chip size="small" color={chipProps.color} icon={chipProps.icon} label={chipProps.label} />
                                            </div>
                                        </div>
                                    </AccordionSummary>

                                    <AccordionDetails>
                                        <div className="flex gap-2 justify-evenly">
                                            <div className="flex flex-col">
                                                <p className="text-sm text-gray-400">Placed By</p>
                                                <p className="text-lg">{order.first_name} {order.last_name}</p>
                                                <p>
                                                {new Date(order.order_date).toLocaleDateString("en-US", {
                                                    month: "long",
                                                    day: "numeric",
                                                    year: "numeric",
                                                })}
                                                </p>

                                            </div>

                                            <div className="border"/>

                                            <div className="flex flex-col">
                                                <p className="text-sm text-gray-400">Shipping</p>
                                                <p>{order.shipping_address.line1}</p>
                                                <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}</p>
                                            </div>

                                            <div className="border"/>

                                            <div className="flex flex-col">
                                                <p className="text-sm text-gray-400">Billing</p>
                                                <p>{order.billing_address.line1}</p>
                                                <p>{order.billing_address.city}, {order.billing_address.state} {order.billing_address.postal_code}</p>
                                            </div>

                                            <div className="border"/>

                                            <div className="flex flex-col">
                                                <p className="text-sm text-gray-400">Payment</p>
                                                <p>
                                                ${order.total_amount.toFixed(2)} with {order?.payment_method_type
                                                    ? order.payment_method_type.charAt(0).toUpperCase() +
                                                    order.payment_method_type.slice(1)
                                                    : ""}
                                                </p>
                                                <p>{order.card_brand?.toUpperCase()} ending in ****{order.card_last4}</p>

                                            </div>
                                        </div>

                                        <div className="p-4 flex justify-end">
                                            <Link to={order ? `/orders/${order.order_number}` : "#"} className="border px-5 py-2 rounded-full">Track Order</Link>
                                        </div>
                                    </AccordionDetails>
                                </Accordion>
                                
                            </div>
                            </>
                        );
                    })}
                </div>
                

            </div>

        </div>
        </>
    );
}