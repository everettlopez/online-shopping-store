import axiosClient from "./axiosClient";

export async function getAllOrders() {
    const res = await axiosClient.get("/orders");
    return res.data;
}

export async function updateOrderStatus(orderId: number, status: string): Promise<void> {
    await axiosClient.put(`/orders/${orderId}/status`, null, { params: { status } });
}

export async function updateOrderTracking(orderId: number, tracking: { tracking_number: string; tracking_carrier: string; tracking_url: string }): Promise<void> {
    await axiosClient.put(`/orders/${orderId}/tracking`, null, { params: tracking });
}

// Tracking without an account: the emailed link carries the order's secret token
export async function getTrackedOrder(orderNumber: string, token: string) {
    const res = await axiosClient.get(`/orders/track/${encodeURIComponent(orderNumber)}`, { params: { token } });
    return res.data;
}

export async function lookUpOrder(orderNumber: string, email: string): Promise<{ order_number: string; access_token: string }> {
    const res = await axiosClient.post("/orders/lookup", { order_number: orderNumber, email });
    return res.data;
}

export function trackingPath(orderNumber: string, token: string) {
    return `/track/${encodeURIComponent(orderNumber)}?token=${encodeURIComponent(token)}`;
}

export async function deleteOrder(orderId: number): Promise<void> {
    await axiosClient.delete(`/orders/${orderId}`);
}

// Refunds through Stripe. Leaving out the amount refunds whatever is left; only a full
// refund can put the items back in stock
export async function refundOrder(orderId: number, refund: { amount?: number; restock: boolean }): Promise<void> {
    await axiosClient.post(`/orders/${orderId}/refund`, refund);
}
