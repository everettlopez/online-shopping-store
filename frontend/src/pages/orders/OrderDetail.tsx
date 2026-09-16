import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import axiosClient from "../../api/axiosClient";

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

export default function OrderDetails() {

    const { order_number } = useParams();
    const [currentOrder, setCurrentOrder] = useState<Order | null>(null);
    const [loading, setLoading] = useState(true);

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

    if (loading) return <p>Loading order...</p>;
    if (!currentOrder) return <p>Order not found.</p>;

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
                    <Link to="/" className="text-xl tracking-widest">ACCOUNT</Link>
                    <Link to="/" className="tracking-wider">SETTINGS</Link>
                </div>

                <div className="flex flex-col items-end">
                    <Link to="/orders" className="text-xl tracking-widest">ORDERS</Link>
                    <Link to="" className="tracking-wider">TRACK</Link>
                    <Link to="" className="tracking-wider">HISTORY</Link>
                </div>

            </div>

            <div className="flex flex-col h-screen bg-gray-100 w-screen p-10 gap-5">
                
                {/* Order Header */}
                <div className="flex gap-10 items-center">
                    <h1 className="text-3xl">ORDER: #{currentOrder.order_number.toUpperCase()}</h1>
                    <p className="text-lg border px-5 rounded-full bg-white">{currentOrder.status.toUpperCase()}</p>
                </div>

                {/* Order Information */}
                <div className="flex justify-evenly">

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

                <div className="p-8 flex flex-col gap-2">
                    {/* Order Items */}
                    {currentOrder.items.map((item) => {
                        const mainImage = item.product?.image_url;
                        return (
                            <>
                            {/* Order Item Card */}
                            <div className="border p-4 flex justify-between">
                                
                                <div className="flex gap-2">
                                    <img src={mainImage} className="h-20 w-20 object-cover"/>
                                    
                                    <div className="flex flex-col">
                                        <p className="text-lg">{item.product.name}</p>
                                        <p>Size: {item.product.size}</p>
                                        <p>Qty: {item.quantity}</p>
                                    </div>
                                </div>
                                
                                <p className="pr-3">${item.product.price.toFixed(2)}</p>
                            </div>
                            </>
                        );
                    })}

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