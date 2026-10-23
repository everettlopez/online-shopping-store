import type { ReactElement } from "react";
import { paymentCardSummary, paymentMethodLabel } from "../../utils/payment";

import AttachMoneyRoundedIcon from '@mui/icons-material/AttachMoneyRounded';
import SettingsRoundedIcon from '@mui/icons-material/SettingsRounded';
import LocalShippingRoundedIcon from '@mui/icons-material/LocalShippingRounded';
import DoneRoundedIcon from '@mui/icons-material/DoneRounded';
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import NotInterestedRoundedIcon from '@mui/icons-material/NotInterestedRounded';
import Stepper from '@mui/material/Stepper';
import { Chip, Step, StepLabel } from "@mui/material";
import OrderAddressLines, { type OrderAddress } from "../OrderAddressLines";
import OrderTotals from "../OrderTotals";

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
  // None for guest orders
  user_id: number | null;
  email?: string | null;

  first_name: string | null;
  last_name: string | null;

  created_at: string;
  updated_at: string;

  shipping_address_id: number | null;
  billing_address_id: number | null;

  order_number: string;
  status: string;
  order_date: string;
  total_amount: number;
  subtotal_amount: number | null;
  shipping_amount: number | null;
  tax_amount: number | null;
  refunded_amount: number;

  payment_intent_id: string | null;
  stripe_session_id: string | null;

  payment_method_type: string | null;
  card_brand: string | null;
  card_last4: string | null;
  payment_status: string | null;
  receipt_url: string | null;

  shipping_address: OrderAddress | null;
  billing_address: OrderAddress | null;

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

const steps = ["Placed", "Processing", "Shipped", "Delivered"];
const stepIndexMap: Record<OrderStatus, number> = { placed: 0, processing: 1, shipped: 2, delivered: 3 };

function OrderStepper({order}: {order: Order}) {
    const activeStep = stepIndexMap[order.status as OrderStatus];

    return (
      <div className="py-4 sm:p-8">
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

// One order's status, tracking, addresses, items and totals. Shown in the account's
// order pages and on the tracking page that guests reach from their emails
export default function OrderView({ order }: { order: Order }) {
    const chipProps = getStatusChipProps(order.status);
    const safeUrl = order.tracking_url?.startsWith("http://") || order.tracking_url?.startsWith("https://") ? order.tracking_url : `https://${order.tracking_url}`; 

    return (
              <div className="flex flex-col border p-4 sm:p-8 rounded-[10px] gap-5 bg-white">
                  {/* Order Header */}
                  <div className="flex flex-wrap gap-x-5 gap-y-2 items-center">
                      <h1 className="text-2xl sm:text-3xl tracking-wider break-all">ORDER: #{order.order_number.toUpperCase()}</h1>
                      <Chip size="small" color={chipProps.color} icon={chipProps.icon} label={chipProps.label} />
                  </div>

                  {order.status !== "completed" && (
                      <OrderStepper order={order}/>
                  )}

                  {/* Order Information: two columns on phones, four in a row from 768 px */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4 md:divide-x [&>div]:md:px-4">

                      {/* User Information */}
                      <div className="flex flex-col">
                          <p className="text-sm text-gray-500">Placed By</p>
                          <p className="text-lg">{order.first_name} {order.last_name}</p>
                          <p>
                          {new Date(order.order_date).toLocaleDateString("en-US", {
                              month: "long",
                              day: "numeric",
                              year: "numeric",
                          })}
                          </p>
                      </div>

                      
                      {/* Shipping */}
                      <div className="flex flex-col">
                          <p className="text-sm text-gray-500">Shipping</p>
                          <OrderAddressLines address={order.shipping_address} />
                      </div>

                      {/* Billing */}
                      <div className="flex flex-col">
                          <p className="text-sm text-gray-500">Billing</p>
                          <OrderAddressLines address={order.billing_address} />
                      </div>

                      {/* Payment */}
                      <div className="flex flex-col">
                          <p className="text-sm text-gray-500">Payment</p>
                          <p>${order.total_amount.toFixed(2)} with {paymentMethodLabel(order.payment_method_type)}</p>
                          {paymentCardSummary(order) && <p>{paymentCardSummary(order)}</p>}

                      </div>
                  </div>

                  {(order.status === "shipped" || order.status === "delivered") && (
                      <>
                      <div className="flex flex-col border gap-2 p-5 rounded-[10px]">
                          <p className="text-lg tracking-wider">TRACKING INFORMATION</p>
                          <div className="flex flex-col">
                              <p>Tracking #: {order.tracking_number?.toUpperCase()}</p>
                              <p>Shipping Carrier: {order.tracking_carrier}</p>
                              <div className="flex flex-wrap gap-x-2">
                                  <p>Tracking URL:</p>
                                  <a href={safeUrl} className="text-gray-600 underline break-all">{order.tracking_url}</a>
                              </div>
                          </div>
                      </div>
                      </>
                  )}

                  <div className="flex flex-col gap-2 py-3">
                      {/* Order Items */}
                      {order.items.map((item) => {
                          const mainImage = item.product?.thumbnail || item.product?.images?.[0];
                          return (
                              /* Order Item Card */
                              <div key={item.order_item_id} className="border p-3 sm:p-4 flex flex-wrap justify-between gap-2 bg-white rounded-[10px]">

                                  <div className="flex gap-2 min-w-0">
                                      {mainImage
                                          ? <img src={mainImage} alt={item.product?.title ?? ""} loading="lazy" className="h-20 w-20 object-cover border rounded-sm shrink-0"/>
                                          : <div className="h-20 w-20 border rounded-sm bg-gray-100 shrink-0"/>}

                                      <div className="flex flex-col min-w-0">
                                          <p className="text-lg">{item.product?.title ?? "Product no longer available"}</p>
                                          {item.product?.size && <p>Size: {item.product.size}</p>}
                                          <p>Qty: {item.quantity}</p>
                                      </div>
                                  </div>

                                  {/* The price paid, not the product's current price */}
                                  <p className="pr-3 tracking-wider">{item.quantity} x ${item.unit_price.toFixed(2)}</p>
                              </div>
                          );
                      })}
                  </div>

                  <div className="p-4">
                      <OrderTotals order={order} />
                  </div>

                  <a href={order.receipt_url ?? "#"} target="_blank" rel="noopener noreferrer" className="flex justify-center border w-fit mx-auto px-5 text-lg py-2 rounded-[10px]">View Receipt</a>
              </div>
    );
}
