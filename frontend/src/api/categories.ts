import axiosClient from "./axiosClient";
import type { Category } from "./admin";

export type { Category };

// Public category list used to build the storefront nav
export async function getStoreCategories(): Promise<Category[]> {
    const res = await axiosClient.get("/categories", { params: { sort: "order" } });
    return res.data.categories;
}
