import axios from "axios";
import axiosClient from "./axiosClient";

export type Category = {
    category_id: number;
    name: string;
    description: string | null;
    sort_order: number;
};

export type AdminUser = {
    user_id: number;
    email: string;
    first_name: string;
    last_name: string;
    created_at: string;
    is_admin: boolean;
};

export type AdminUserInput = {
    email: string;
    first_name: string;
    last_name: string;
    is_admin: boolean;
    password?: string;
};

// Pull the FastAPI "detail" message out of a failed request
export function apiErrorMessage(err: unknown, fallback = "Something went wrong"): string {
    if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === "string") return detail;
    }
    return fallback;
}

// Categories
export async function getCategories(): Promise<Category[]> {
    const res = await axiosClient.get("/categories", { params: { sort: "order" } });
    return res.data.categories;
}

// Saves the nav order: every category id, first to last
export async function reorderCategories(categoryIds: number[]): Promise<Category[]> {
    const res = await axiosClient.put("/categories/reorder", { category_ids: categoryIds });
    return res.data.categories;
}

export async function createCategory(data: { name: string; description: string | null }): Promise<Category> {
    const res = await axiosClient.post("/categories", data);
    return res.data;
}

export async function updateCategory(categoryId: number, data: { name?: string; description?: string | null }): Promise<Category> {
    const res = await axiosClient.put(`/categories/${categoryId}`, data);
    return res.data;
}

export async function deleteCategory(categoryId: number): Promise<void> {
    await axiosClient.delete(`/categories/${categoryId}`);
}

// Users
export async function getUsers(): Promise<AdminUser[]> {
    const res = await axiosClient.get("/admin/users");
    return res.data.users;
}

export async function createUser(data: AdminUserInput): Promise<AdminUser> {
    const res = await axiosClient.post("/admin/users", data);
    return res.data;
}

export async function updateUser(userId: number, data: Partial<AdminUserInput>): Promise<AdminUser> {
    const res = await axiosClient.put(`/admin/users/${userId}`, data);
    return res.data;
}

export async function deleteUser(userId: number): Promise<void> {
    await axiosClient.delete(`/admin/users/${userId}`);
}
