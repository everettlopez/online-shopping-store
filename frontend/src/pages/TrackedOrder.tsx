import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { getTrackedOrder } from "../api/orders";
import Navbar from "../components/Navbar";
import OrderView, { type Order } from "../components/orders/OrderView";

// An order opened from the private link in its emails (or found on /track), no login needed
export default function TrackedOrder() {
    const { order_number } = useParams();
    const [params] = useSearchParams();
    const token = params.get("token") ?? "";

    // Tagged with the link it was loaded for, so a new link never shows the old order
    const linkKey = `${order_number}|${token}`;
    const [loaded, setLoaded] = useState<{ key: string; order: Order | null } | null>(null);

    useEffect(() => {
        if (!order_number) return;
        let cancelled = false;

        getTrackedOrder(order_number, token)
            .then((order) => { if (!cancelled) setLoaded({ key: linkKey, order }); })
            .catch((err) => {
                console.error("Failed to load order:", err);
                if (!cancelled) setLoaded({ key: linkKey, order: null });
            });

        return () => { cancelled = true; };
    }, [order_number, token, linkKey]);

    const loading = loaded?.key !== linkKey;
    const order = loading ? null : loaded.order;

    return (
        <>
        <Navbar />
        <div className="flex flex-col h-fit gap-5 bg-gray-100 p-8">
            {loading ? (
                <p>Loading order...</p>
            ) : order ? (
                <OrderView order={order} />
            ) : (
                <div className="flex flex-col items-center gap-3 bg-white border rounded-[10px] p-8">
                    <p className="text-lg">We couldn't find that order.</p>
                    <p className="text-gray-500">The link may be incomplete. You can look the order up with its number and your email instead.</p>
                    <Link to="/track" className="border py-2 px-5 rounded-[5px]">Find my order</Link>
                </div>
            )}
        </div>
        </>
    );
}
