import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axiosClient from "../../api/axiosClient";

import Navbar from "../../components/Navbar";
import AccountNav from "../../components/AccountNav";
import { ErrorState, LoadingState } from "../../components/Status";
import OrderView, { type Order } from "../../components/orders/OrderView";

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

    return (
        <>
        {/* Header */}
        <Navbar />
        <main>

        {/* Column Setup */}
        <div className="flex flex-col md:flex-row px-4 py-6 md:p-8 gap-6">
            <AccountNav />

            <div className="flex flex-col flex-1 min-w-0 h-fit gap-5 bg-gray-100 p-3 sm:p-8 rounded-[10px]">
                {loading ? (
                    <LoadingState label="Loading order" />
                ) : currentOrder ? (
                    <OrderView order={currentOrder} />
                ) : (
                    <ErrorState message="We couldn't find that order." />
                )}
            </div>
        </div>
        </main>
        </>
    );
}
