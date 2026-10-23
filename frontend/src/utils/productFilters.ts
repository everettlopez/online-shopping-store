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
    return activeFilterCount(filters) > 0 || filters.sort !== defaultSort;
}

// Ticked sizes and colors, plus one for a price range; the Filter button shows it on phones
export function activeFilterCount(filters: ProductFilterState): number {
    return filters.sizes.length + filters.colors.length
        + (filters.minPrice !== "" || filters.maxPrice !== "" ? 1 : 0);
}

// The filters live in the URL query (size, color, min, max, order) so a product page's
// back link and the browser's Back button return to the same grid. "order" is the
// dropdown's sort; "sort=newest" is the separate New Arrivals view the header links to.
const SORTS: ProductSort[] = ["featured", "newest", "price-asc", "price-desc"];
const FILTER_PARAMS = ["size", "color", "min", "max", "order"];

export function filtersFromParams(params: URLSearchParams, defaultSort: ProductSort): ProductFilterState {
    const order = params.get("order") as ProductSort | null;
    return {
        sizes: params.getAll("size").map((value) => value.toLowerCase()),
        colors: params.getAll("color").map((value) => value.toLowerCase()),
        minPrice: params.get("min") ?? "",
        maxPrice: params.get("max") ?? "",
        sort: order && SORTS.includes(order) ? order : defaultSort,
    };
}

// The current query with its filter params replaced by these filters (defaults left out)
export function paramsWithFilters(params: URLSearchParams, filters: ProductFilterState, defaultSort: ProductSort): URLSearchParams {
    const next = new URLSearchParams(params);
    FILTER_PARAMS.forEach((name) => next.delete(name));

    filters.sizes.forEach((size) => next.append("size", size));
    filters.colors.forEach((color) => next.append("color", color));
    if (filters.minPrice !== "") next.set("min", filters.minPrice);
    if (filters.maxPrice !== "") next.set("max", filters.maxPrice);
    if (filters.sort !== defaultSort) next.set("order", filters.sort);

    return next;
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
