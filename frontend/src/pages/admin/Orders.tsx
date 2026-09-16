import type { ReactElement } from "react";

import { Link } from "react-router-dom";
import { DataGrid } from "@mui/x-data-grid";
import { useEffect, useState } from "react";
import axiosClient from "../../api/axiosClient";
import ConfirmDeleteOrderModal from "../../components/admin/orders/ConfirmDeleteOrderModal";

import { Chip, FormControl, InputLabel, MenuItem, Select } from "@mui/material";

import Box from '@mui/material/Box';
import AttachMoneyRoundedIcon from '@mui/icons-material/AttachMoneyRounded';
import SettingsRoundedIcon from '@mui/icons-material/SettingsRounded';
import LocalShippingRoundedIcon from '@mui/icons-material/LocalShippingRounded';
import DoneRoundedIcon from '@mui/icons-material/DoneRounded';
import DoneAllRoundedIcon from '@mui/icons-material/DoneAllRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import NotInterestedRoundedIcon from '@mui/icons-material/NotInterestedRounded';
import TextField from '@mui/material/TextField';

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


export default function AdminOrders() 
{

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  function openDeleteModal() {
    setDeleteModalOpen(true);
  }

  function closeDeleteModal() {
    setDeleteModalOpen(false);
  }

  function confirmDeleteOrder() {
    handleDeleteOrder();
    closeDeleteModal();
  }



  const [rows, setRows] = useState([]);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [fullOrders, setFullOrders] = useState<Order[]>([]);

  // --- COLUMNS ---
  const columns = [
    { field: "id", headerName: "Order ID", width: 100, resizable: false,},
    { field: "order_number", headerName: "Order #", width: 150, resizable: false,},
    { field: "user_id", headerName: "User ID", width: 100, resizable: false,},
    { field: "first_name", headerName: "First Name", width: 150, resizable: false,},
    { field: "last_name", headerName: "Last Name", width: 150, resizable: false,},
    { field: "status", headerName: "Order Status", width: 150, resizable: false, editable: true, renderCell: (params: any) => {
      const chipProps = getStatusChipProps(params.value);
      return (
        <div className="flex w-full">
          <Chip
            size="small"
            color={chipProps.color}
            icon={chipProps.icon}
            label={chipProps.label}
          />
      </div>
      );
    }},
    { field: "total_amount", headerName: "Total ($)", width: 120, resizable: false, valueFormatter: (params: any) => params.value },
    { field: "created_at", headerName: "Created", width: 200, resizable: false,},
    { field: "expand", headerName: "", width: 80, resizable: false, sortable: false, renderCell: (params: any) => (
      <button className="text-blue-600 underline" onClick={() => setExpandedRow(expandedRow === params.row.id ? null : params.row.id)}>
        {expandedRow === params.row.id ? "Hide" : "View"}
      </button>
    )}
  ];

  const [selectedStatus, setSelectedStatus] = useState("");

  function handleStatusStateChange(e: any) {
    setSelectedStatus(e.target.value);
  }

  function handleCancel() {
    setSelectedStatus(""); // revert selection
  }

  async function handleOrderStatusChange() {
    if (!expandedRow) return;
    try 
    {
      await axiosClient.put(`/orders/${expandedRow}/status`, null, {
        params: {
          status: selectedStatus
        }
      });

      await fetchOrders();
      handleCancel();
      console.log("Updated order:", expandedRow, "to", selectedStatus);
    }
    catch (err)
    {
      console.error("Failed to update order status: ", err);
    }
  }

  async function fetchOrders() {
    try {
      const response = await axiosClient.get("/orders");

      setFullOrders(response.data);

      const formatted = response.data.map((order: Order) => ({
        id: order.order_id,
        user_id: order.user_id,
        first_name: order.first_name,
        last_name: order.last_name,
        order_number: order.order_number.toUpperCase(),
        status: order.status,
        total_amount: order.total_amount.toFixed(2),
        created_at: new Date(order.created_at).toLocaleString()
      }));

      setRows(formatted);
    } catch (err) {
      console.error("Failed to fetch orders: ", err);
    }
  }

  async function handleCompleteOrder() {
    try 
    {
      await axiosClient.put(`/orders/${expandedRow}/status`, null, {
        params: {
          status: "completed"
        }
      });

      await fetchOrders();
      console.log("Updated order:", expandedRow, "to", "completed");
    }
    catch (err)
    {
      console.error("Failed to complete the order: ", err);
    }
  }

  async function handleDeleteOrder()
  {
    try 
    {
      await axiosClient.delete(`/orders/${expandedRow}`);
      await fetchOrders();
      console.log("Delete order: ", expandedRow);
    }
    catch (err)
    {
      console.error("Failed to delete the order: ", err);
    }
  }

  // --- FETCH ORDERS ---
  useEffect(() => {

    fetchOrders();
  }, []);

  return (
    <>
    {/* Confirm Delete Modal */}


    {/* Header */}
    <div className="relative flex flex-col max-w-screen justify-center items-center gap-4 p-5">

        {/* Logo */}
        <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

        {/* Navigation */}
        <nav className="flex gap-12">
            <Link to="/admin/products"><p className="text-base font-normal tracking-widest">PRODUCTS</p></Link>
            <Link to="/admin/categories"><p className="text-base font-normal tracking-widest">CATEGORIES</p></Link>
            <Link to="/admin/users"><p className="text-base font-normal tracking-widest">USERS</p></Link>
            <Link to="/admin/orders"><p className="text-base font-normal tracking-widest">ORDERS</p></Link>
        </nav>
    </div>

  

      <div className="flex flex-col max-h-screen max-w-screen p-10 gap-4">

        {/* Orders Table */}
        <h1 className="text-4xl tracking-wider">ORDERS</h1>
        <div className="h-fit"> 
          <DataGrid
            rows={rows}
            columns={columns}
            checkboxSelection
            sx={{
              "& .MuiDataGrid-cell": {
                padding: "0 8px",        // remove giant padding
                lineHeight: "1.2rem",    // shrink row height
                display: "flex",
                alignItems: "center",
              }
            }}
          />
        </div>

        {/* Order Details */}
        <div className="">
          {expandedRow && (
            <Box className="flex flex-col border p-4 gap-2">

              {/* Find the full order object */}
              {(() => {
                const order = fullOrders.find(o => o.order_id === expandedRow);
                if (!order) return null;

                const chipProps = getStatusChipProps(order.status);

                return (
                  <>
                    {/* Order Header */}
                    <div className="flex gap-4 items-center">
                      <h1 className="text-2xl tracking-wider">ORDER: #{order.order_number.toUpperCase()}</h1>
                      <Chip 
                        size="small"
                        color={chipProps.color}
                        icon={chipProps.icon}
                        label={chipProps.label}/>
                    </div>
                    
                    {/* Order Information */}
                    <div className="flex justify-evenly items-center py-6">
                      {/* User Information */}
                      <div className="flex flex-col">
                        <p className="text-gray-400 text-sm tracking-wider">USER</p>
                        <p>{order.first_name} {order.last_name}</p>
                        <p>User ID: {order.user_id}</p>
                      </div>

                      <div className="border"/>

                      {/* Shipping */}
                      <div className="flex flex-col">
                        <p className="text-gray-400 text-sm tracking-wider">SHIPPING</p>
                        <p>{order.shipping_address.line1}</p>
                        <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}</p>
                      </div>

                      <div className="border"/>

                      {/* Billing */}
                      <div className="flex flex-col">
                        <p className="text-gray-400 text-sm tracking-wider">BILLING</p>
                        <p>{order.billing_address.line1}</p>
                        <p>{order.billing_address.city}, {order.billing_address.state} {order.billing_address.postal_code}</p>
                      </div>

                      <div className="border"/>

                      {/* Payment */}
                      <div className="flex flex-col">
                        <p className="text-gray-400 text-sm tracking-wider">PAYMENT</p>
                        <p>${order.total_amount.toFixed(2)} paid with {order.payment_method_type?.toUpperCase()}</p>
                        <p>{order.card_brand?.toUpperCase()} ending in ****{order.card_last4}</p>
                      </div>
                    </div>

                    {/* Order Items */}
                    <div className="flex flex-col justify-center items-center p-8 gap-5 border rounded-[10px]">

                      <div className="flex flex-col gap-1 w-full">
                        {order.items.map((items) => {
                          return (
                            <div className="flex justify-between w-full p-3 items-center rounded-[10px]">
                              <div className="flex gap-4">
                                <img src={items.product.image_url} className="w-20 h-20 object-cover border rounded"/>
                                <div className="flex flex-col">
                                  <p className="text-lg tracking-wider">{items.product.name}</p>
                                  <p className="text-gray-400 tracking-wider">${items.product.price.toFixed(2)}</p>
                                  <p className="text-gray-400 tracking-wider">Qty: {items.quantity}</p>
                                </div>
                              </div>

                              <p className="text-lg tracking-wider">{items.quantity} x ${items.product.price.toFixed(2)}</p>
                            </div>
                          );
                        })}  
                      </div>       

                      <div className="flex gap-10 w-full justify-end pr-2 items-center">
                        <p className="text-lg tracking-wider">TOTAL:</p>
                        <p className="text-lg tracking-wider">${order.total_amount.toFixed(2)}</p>
                      </div>             

                    </div>

                    {/* Order Functions (i.e. Edit Status) */}
                    <div className="flex flex-col py-4 gap-5">

                      {/* Update Order Status Form */}
                      <form className="border py-2 px-5 rounded-[10px] flex gap-3 items-center justify-between">
                        
                        <div className="flex items-center gap-6">
                          <p className="text-lg tracking-wider">UPDATE ORDER STATUS: </p>

                          <div className="flex gap-8 justify-evenly py-4">

                            <div className={`flex gap-2 items-center border px-5 rounded ${selectedStatus === "placed" ? "bg-gray-200" : "bg-white"}`}>
                              <label htmlFor="placed" className="tracking-wider">Placed</label>
                              <input id="placed" name="orderStatus" type="radio" checked={selectedStatus === "placed"} onChange={handleStatusStateChange} value="placed" className="checked:bg-green-500 checked:border-green-500"></input>
                            </div>

                            <div className={`flex gap-2 items-center border px-5 rounded ${selectedStatus === "processing" ? "bg-gray-200" : "bg-white"}`}>
                              <label htmlFor="processing" className="tracking-wider">Processing</label>
                              <input id="processing" name="orderStatus" type="radio" checked={selectedStatus === "processing"} onChange={handleStatusStateChange} value="processing"></input>
                            </div>

                            <div className={`flex gap-2 items-center border px-5 rounded ${selectedStatus === "shipped" ? "bg-gray-200" : "bg-white"}`}>
                              <label htmlFor="shipped" className="tracking-wider">Shipped</label>
                              <input id="shipped" name="orderStatus" type="radio" checked={selectedStatus === "shipped"} onChange={handleStatusStateChange} value="shipped"></input>
                            </div>

                            <div className={`flex gap-2 items-center border px-5 rounded ${selectedStatus === "delivered" ? "bg-gray-200" : "bg-white"}`}>
                              <label htmlFor="delivered" className="tracking-wider">Delivered</label>
                              <input id="delivered" name="orderStatus" type="radio" checked={selectedStatus === "delivered"} onChange={handleStatusStateChange} value="delivered"></input>
                            </div>
                          </div>
                        </div>

                        <div className="flex gap-4 justify-end">
                          <button className="border px-5 py-1 rounded-full hover:bg-gray-100 hover:border-0" type="button" onClick={handleCancel}>Cancel</button>
                          <button 
                            type="button" disabled={!selectedStatus} onClick={handleOrderStatusChange} className="bg-green-300 px-5 py-1 rounded-full disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 hover:border-0">Save</button>
                        </div>
                      </form>

                      {/* Update Tracking Information (Status == Processing) */}
                      {order.status == "processing" && (
                        <div className="p-4 border rounded-[10px] flex flex-col items-center gap-4">
                          <p className="text-lg tracking-wider flex justify-start w-full">ADD TRACKING INFORMATION</p>
                          <div className="flex items-center w-full gap-4">

                            <TextField
                              id="tracking_number"
                              required
                              label="Tracking Number"
                              sx={{ width: "450px" }}
                            />

                            <FormControl sx={{ width: "200px" }}>
                              <InputLabel id="tracking_carrier_label">Carrier</InputLabel>

                              <Select
                                labelId="tracking_carrier_label"
                                id="tracking_carrier"
                                label="Shipping Carrier"
                                required
                              >
                                <MenuItem value="USPS">USPS</MenuItem>
                                <MenuItem value="UPS">UPS</MenuItem>
                                <MenuItem value="FedEx">FedEx</MenuItem>
                                <MenuItem value="DHL">DHL</MenuItem>
                              </Select>
                            </FormControl>

                            <TextField id="tracking_url" required label="Tracking URL" className="w-full"/>
                          </div>

                          <div className="flex gap-4 justify-end w-full">
                            <button className="border px-5 py-1 rounded-full hover:bg-gray-100 hover:border-0">Cancel</button>
                            <button disabled className="bg-green-300 px-5 py-1 rounded-full disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 hover:border-0">Add Tracking</button>
                          </div>
                        </div>

                      )}
                    </div>


                    <div className="flex justify-between">
                      <button onClick={() => openDeleteModal()} className="border px-5 py-1 rounded-full bg-red-400 text-white">Delete Order</button>
                      <button className="bg-green-300 px-5 py-1 rounded-full disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100" disabled={order.status !== "delivered"} onClick={handleCompleteOrder}>Complete Order</button>
                    </div>
                  </>
                );
              })()}
            </Box>
          )}
        </div>

      </div>

      <ConfirmDeleteOrderModal
        open={deleteModalOpen}
        onClose={closeDeleteModal}
        onConfirm={confirmDeleteOrder}
      />

    </>
  );
}
