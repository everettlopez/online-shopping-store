import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import axiosClient from "../../api/axiosClient";
import { useAuth } from "../../context/AuthContext";

import Navbar from "../../components/Navbar";
import OrderView, { type Order } from "../../components/orders/OrderView";

export default function OrderDetails() {
    const { user } = useAuth();
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
        <Navbar />

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
                    <Link to="/orders" className="tracking-wider">TRACK</Link>
                    <Link to="" className="tracking-wider">HISTORY</Link>
                </div>

            </div>

            <div className="flex flex-col w-screen h-fit gap-5 bg-gray-100 p-8">
                <OrderView order={currentOrder} />
            </div>

        </div>
        </>
    );
}
