import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import axiosClient from "../../api/axiosClient";

import Navbar from "../../components/Navbar";
import AccountNav from "../../components/AccountNav";
import { EmptyState, ErrorState, LoadingState } from "../../components/Status";
import OrderView, { type Order } from "../../components/orders/OrderView";

export default function OrderDetails() {
    const { order_number } = useParams();
    // Keyed by the order and attempt it was fetched for, so a new order or "Try again" shows loading
    const [loaded, setLoaded] = useState<{ key: string; order: Order | null; failed: boolean } | null>(null);
    const [attempt, setAttempt] = useState(0);
    const key = `${order_number}|${attempt}`;

    useEffect(() => {
        if (!order_number) return;

        let cancelled = false;
        axiosClient.get<Order>(`/orders/${order_number}`)
            .then((response) => { if (!cancelled) setLoaded({ key, order: response.data, failed: false }); })
            .catch((err) => {
                if (cancelled) return;
                // A 404 is an order that isn't this account's; anything else can be retried
                const missing = axios.isAxiosError(err) && err.response?.status === 404;
                if (!missing) console.error("Failed to load current order: ", err);
                setLoaded({ key, order: null, failed: !missing });
            });

        return () => { cancelled = true; };
    }, [order_number, key]);

    const current = loaded?.key === key ? loaded : null;

    return (
        <>
        {/* Header */}
        <Navbar />
        <main>

        {/* Column Setup */}
        <div className="flex flex-col md:flex-row px-4 py-6 md:p-8 gap-6">
            <AccountNav />

            <div className="flex flex-col flex-1 min-w-0 h-fit gap-5 bg-gray-100 p-3 sm:p-8 rounded-[10px]">
                {!current ? (
                    <LoadingState label="Loading order" />
                ) : current.order ? (
                    <OrderView order={current.order} />
                ) : current.failed ? (
                    <ErrorState message="We couldn't load this order." onRetry={() => setAttempt((n) => n + 1)} />
                ) : (
                    <EmptyState title="We couldn't find that order" action={{ to: "/orders", label: "See your orders" }} />
                )}
            </div>
        </div>
        </main>
        </>
    );
}
