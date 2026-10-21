import axiosClient from "./axiosClient";

export async function getAllProducts() {
    const res = await axiosClient.get("/products");
    return res.data;
}

export async function createProduct(formData: FormData) {
    const res = await axiosClient.post("/products", formData);
    return res.data;
}

export async function updateProduct(productId: number, formData: FormData) {
    const res = await axiosClient.put(`/products/${productId}`, formData);
    return res.data;
}

export async function deleteProduct(productId: number): Promise<void> {
    await axiosClient.delete(`/products/${productId}`);
}
