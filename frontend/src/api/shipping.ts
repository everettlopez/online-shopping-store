import axiosClient from "./axiosClient";

export interface ShippingRates {
    flat_rate: number;
    free_shipping_threshold: number;
}

// The store's shipping prices (SHIPPING_FLAT_RATE and FREE_SHIPPING_THRESHOLD on the API)
export async function getShippingRates(): Promise<ShippingRates> {
    const res = await axiosClient.get("/payments/shipping");
    return res.data;
}
