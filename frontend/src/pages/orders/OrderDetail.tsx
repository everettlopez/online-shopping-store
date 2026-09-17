import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import axiosClient from "../../api/axiosClient";
import { useAuth } from "../../context/AuthContext";

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
import { Chip, FormControl, InputLabel, MenuItem, Select, Step, StepLabel } from "@mui/material";

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

  tracking_number: string | null;
  tracking_carrier: string | null;
  tracking_url: string | null;

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

export default function OrderDetails() {
    const { user } = useAuth();
    const { order_number } = useParams();
    const [currentOrder, setCurrentOrder] = useState<Order | null>(null);
    const [loading, setLoading] = useState(true);

    const steps = ["Placed", "Processing", "Shipped", "Delivered"];
    const stepIndexMap: Record<OrderStatus, number> = { placed: 0, processing: 1, shipped: 2, delivered: 3 };

    useEffect(() => {
        async function fetchOrder() {
            try 
            {
                const response = await axiosClient.get(`/orders/${order_number}`);
                setCurrentOrder(response.data);
            }
            catch (err)
            {
                console.error("Failed to load current order: ", err);
            }
            finally 
            {
                setLoading(false);
            }
        }
        
        if (order_number) fetchOrder();
    }, [order_number]);

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

    if (loading) return <p>Loading order...</p>;
    if (!currentOrder) return <p>Order not found.</p>;

    const chipProps = getStatusChipProps(currentOrder.status);
    const safeUrl = currentOrder.tracking_url?.startsWith("http://") || currentOrder.tracking_url?.startsWith("https://") ? currentOrder.tracking_url : `https://${currentOrder.tracking_url}`; 

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

        {/* Column Setup */}
        <div className="flex h-screen p-8 gap-5">

            {/* Account / User Navigation */}
            <div className="flex flex-col h-screen p-10 gap-4">

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

            <div className="flex flex-col w-screen h-fit gap-5 bg-gray-100 p-8">
                
                <div className="flex flex-col border p-8 rounded-[10px] gap-5 bg-white">
                    {/* Order Header */}
                    <div className="flex gap-5 items-center">
                        <h1 className="text-3xl tracking-wider">ORDER: #{currentOrder.order_number.toUpperCase()}</h1>
                        <Chip size="small" color={chipProps.color} icon={chipProps.icon} label={chipProps.label} />
                    </div>

                    {currentOrder.status !== "completed" && (
                        <OrderStepper order={currentOrder}/>
                    )}

                    {/* Order Information */}
                    <div className="flex justify-evenly py-4">

                        {/* User Information */}
                        <div className="flex flex-col">
                            <p className="text-sm text-gray-400">Placed By</p>
                            <p className="text-lg">{currentOrder.first_name} {currentOrder.last_name}</p>
                            <p>
                            {new Date(currentOrder.order_date).toLocaleDateString("en-US", {
                                month: "long",
                                day: "numeric",
                                year: "numeric",
                            })}
                            </p>
                        </div>

                        <div className="border"/>
                        
                        {/* Shipping */}
                        <div className="flex flex-col">
                            <p className="text-sm text-gray-400">Shipping</p>
                            <p>{currentOrder.shipping_address.line1}</p>
                            <p>{currentOrder.shipping_address.city}, {currentOrder.shipping_address.state} {currentOrder.shipping_address.postal_code}</p>
                        </div>

                        <div className="border"/>

                        {/* Billing */}
                        <div className="flex flex-col">
                            <p className="text-sm text-gray-400">Billing</p>
                            <p>{currentOrder.billing_address.line1}</p>
                            <p>{currentOrder.billing_address.city}, {currentOrder.billing_address.state} {currentOrder.billing_address.postal_code}</p>
                        </div>

                        <div className="border"/>

                        {/* Payment */}
                        <div className="flex flex-col">
                            <p className="text-sm text-gray-400">Payment</p>
                            <p>
                            ${currentOrder.total_amount.toFixed(2)} with {currentOrder?.payment_method_type
                                ? currentOrder.payment_method_type.charAt(0).toUpperCase() +
                                currentOrder.payment_method_type.slice(1)
                                : ""}
                            </p>
                            <p>{currentOrder.card_brand?.toUpperCase()} ending in ****{currentOrder.card_last4}</p>

                        </div>
                    </div>

                    {(currentOrder.status === "shipped" || currentOrder.status === "delivered") && (
                        <>
                        <div className="flex flex-col border gap-2 p-5 rounded-[10px]">
                            <p className="text-lg tracking-wider">TRACKING INFORMATION</p>
                            <div className="flex flex-col">
                                <p>Tracking #: {currentOrder.tracking_number?.toUpperCase()}</p>
                                <p>Shipping Carrier: {currentOrder.tracking_carrier}</p>
                                <div className="flex gap-2">
                                    <p>Tracking URL:</p>
                                    <a href={safeUrl} className="text-gray-400">{currentOrder.tracking_url}</a>
                                </div>
                            </div>
                        </div>
                        </>
                    )}

                    <div className="flex flex-col gap-2 py-3">
                        {/* Order Items */}
                        {currentOrder.items.map((item) => {
                            const mainImage = item.product?.image_url;
                            return (
                                <>
                                {/* Order Item Card */}
                                <div className="border p-4 flex justify-between bg-white rounded-[10px]">
                                    
                                    <div className="flex gap-2">
                                        <img src={mainImage} className="h-20 w-20 object-cover border rounded"/>
                                        
                                        <div className="flex flex-col">
                                            <p className="text-lg">{item.product.name}</p>
                                            <p>Size: {item.product.size}</p>
                                            <p>Qty: {item.quantity}</p>
                                        </div>
                                    </div>
                                    
                                    <p className="pr-3 tracking-wider">{item.quantity} x ${item.product.price.toFixed(2)}</p>
                                </div>
                                </>
                            );
                        })}
                    </div>

                    <div className="flex justify-evenly p-4">
                        <p>Total: </p>
                        <p>${currentOrder.total_amount.toFixed(2)}</p>
                    </div>

                    <a href={currentOrder.receipt_url ?? "#"} target="_blank" rel="noopener noreferrer" className="flex justify-center border w-fit mx-auto px-5 text-lg py-2 rounded-[10px]">View Receipt</a>
                </div>

                
            </div>

        </div>
        </>
    );
}