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

export async function deleteOrder(orderId: number): Promise<void> {
    await axiosClient.delete(`/orders/${orderId}`);
}
