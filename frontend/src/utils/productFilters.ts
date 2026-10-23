// Client-side filtering and sorting for the product grid on /products
import { compareSizes } from "./productOptions";

export type ProductSort = "featured" | "newest" | "price-asc" | "price-desc";

export interface ProductFilterState {
    sizes: string[];    // lower-cased values
    colors: string[];   // lower-cased values
    minPrice: string;
    maxPrice: string;
    sort: ProductSort;
}

export interface FilterableProduct {
    price: number;
    size?: string | null;
    color?: string | null;
    created_at: string;
}

export interface FilterOption {
    value: string;  // lower-cased, used for matching
    label: string;  // first spelling seen, shown to the shopper
}

export function defaultProductFilters(sort: ProductSort = "featured"): ProductFilterState {
    return { sizes: [], colors: [], minPrice: "", maxPrice: "", sort };
}

export function hasActiveFilters(filters: ProductFilterState, defaultSort: ProductSort): boolean {
    return filters.sizes.length > 0 || filters.colors.length > 0
        || filters.minPrice !== "" || filters.maxPrice !== ""
        || filters.sort !== defaultSort;
}

// Distinct non-empty values of a product field, compared case-insensitively
export function filterOptions<T extends FilterableProduct>(products: T[], field: "size" | "color"): FilterOption[] {
    const options = new Map<string, string>();

    for (const product of products) {
        const label = product[field]?.trim();
        if (!label) continue;

        const value = label.toLowerCase();
        if (!options.has(value)) options.set(value, label);
    }

    // Sizes in their natural order (S, M, L), colors A-Z
    const compare = field === "size" ? compareSizes : (a: string, b: string) => a.localeCompare(b);
    return [...options].map(([value, label]) => ({ value, label })).sort((a, b) => compare(a.label, b.label));
}

// Ticked values within a group match any of them; different groups must all match
export function applyProductFilters<T extends FilterableProduct>(products: T[], filters: ProductFilterState): T[] {
    const minPrice = filters.minPrice === "" ? null : Number(filters.minPrice);
    const maxPrice = filters.maxPrice === "" ? null : Number(filters.maxPrice);

    const visible = products.filter((product) => {
        const size = product.size?.trim().toLowerCase() ?? "";
        const color = product.color?.trim().toLowerCase() ?? "";

        if (filters.sizes.length > 0 && !filters.sizes.includes(size)) return false;
        if (filters.colors.length > 0 && !filters.colors.includes(color)) return false;
        if (minPrice !== null && !Number.isNaN(minPrice) && product.price < minPrice) return false;
        if (maxPrice !== null && !Number.isNaN(maxPrice) && product.price > maxPrice) return false;

        return true;
    });

    switch (filters.sort) {
        case "newest":
            return visible.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        case "price-asc":
            return visible.sort((a, b) => a.price - b.price);
        case "price-desc":
            return visible.sort((a, b) => b.price - a.price);
        default:
            return visible;
    }
}
