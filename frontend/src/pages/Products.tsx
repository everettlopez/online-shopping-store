import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import { useCategories } from "../context/useCategories";
import Drawer from "../components/Drawer";
import Navbar from "../components/Navbar";
import ProductCard from "../components/products/ProductCard";
import ProductFilters from "../components/products/ProductFilters";
import { ErrorState, LoadingState } from "../components/Status";
import { activeFilterCount, applyProductFilters, defaultProductFilters, filterOptions, filtersFromParams, hasActiveFilters, paramsWithFilters, type ProductFilterState } from "../utils/productFilters";

export interface Product {
  product_id: number;
  category: { category_id: number; name: string };

  title: string;  // Updated
  description?: string;
  price: number;
  size?: string;
  color?: string;
  thumbnail?: string;   // Updated
  stock_quantity: number;
  is_active: boolean;

  images?: string[];
  created_at: string;
}

export default function Products() {

    // Products are tagged with the URL query they were fetched for, so switching
    // categories never shows the previous category's products under the new heading
    const [loaded, setLoaded] = useState<{ key: string; products: Product[]; failed?: boolean } | null>(null);
    // Bumped by "Try again", which makes it a new fetch
    const [attempt, setAttempt] = useState(0);
    const [filtersOpen, setFiltersOpen] = useState(false);
    const closeFilters = useCallback(() => setFiltersOpen(false), []);

    const [searchParams, setSearchParams] = useSearchParams();
    const { categories, loading: loadingCategories } = useCategories();

    const categoryParam = searchParams.get("category");
    const isNewArrivals = searchParams.get("sort") === "newest";
    const categoryId = categoryParam !== null && /^\d+$/.test(categoryParam) ? Number(categoryParam) : null;
    const currentCategory = categories.find((category) => category.category_id === categoryId);
    const categoryNotFound = categoryParam !== null && !loadingCategories && !currentCategory;

    const productsKey = `${categoryId ?? "all"}|${isNewArrivals ? "newest" : ""}|${attempt}`;
    const loadingProducts = loaded?.key !== productsKey;
    const products = useMemo(() => (loaded?.key === productsKey ? loaded.products : []), [loaded, productsKey]);
    const loadFailed = !loadingProducts && loaded?.failed === true;

    // Filters are kept in the URL query, so the header's links (which carry none) reset them
    // and coming back from a product page restores them. Replacing, not pushing, keeps each
    // tick or keystroke out of the browser history.
    const defaultSort = isNewArrivals ? "newest" : "featured";
    const filters = useMemo(() => filtersFromParams(searchParams, defaultSort), [searchParams, defaultSort]);
    const setFilters = (next: ProductFilterState) =>
        setSearchParams(paramsWithFilters(searchParams, next, defaultSort), { replace: true });
    const clearFilters = () => setFilters(defaultProductFilters(defaultSort));
    const filterCount = activeFilterCount(filters);

    const sizeOptions = useMemo(() => filterOptions(products, "size"), [products]);
    const colorOptions = useMemo(() => filterOptions(products, "color"), [products]);
    const visibleProducts = useMemo(() => applyProductFilters(products, filters), [products, filters]);

    let heading = "ALL PRODUCTS";
    if (isNewArrivals) heading = "NEW ARRIVALS";
    else if (currentCategory) heading = currentCategory.name.toUpperCase();

    // Fetch Products for the selected category (or newest / all) whenever the nav changes the URL
    useEffect(() => {
        if (categoryParam !== null && categoryId === null) return;

        let cancelled = false;
        axiosClient.get("/products/active", {
            params: {
                category_id: categoryId ?? undefined,
                sort: isNewArrivals ? "newest" : undefined,
                limit: isNewArrivals ? 24 : undefined,
            },
        })
            .then((response) => { if (!cancelled) setLoaded({ key: productsKey, products: response.data }); })
            .catch((err) => {
                console.error("Failed to fetch products: ", err);
                if (!cancelled) setLoaded({ key: productsKey, products: [], failed: true });
            });

        return () => { cancelled = true; };
    }, [categoryId, categoryParam, isNewArrivals, productsKey]);

    return (
        <>
        {/* Header */}
        <Navbar />
        <main>

        {/* Main */}
        <div className="flex gap-6 px-4 pb-8 md:p-8">
            
            {/* Filter Section: a sidebar from 768 px, a drawer below */}
            <ProductFilters
                filters={filters}
                sizeOptions={sizeOptions}
                colorOptions={colorOptions}
                canClear={hasActiveFilters(filters, defaultSort)}
                onChange={setFilters}
                onClear={clearFilters}
            />

            {/* Products Grid */}
            <div className="flex flex-col gap-4 flex-1 min-w-0">
            <div className="flex items-center justify-between gap-4">
                <h2 className="text-xl md:text-2xl tracking-widest">{categoryNotFound ? "CATEGORY NOT FOUND" : heading}</h2>
                {!categoryNotFound && (
                    <button
                        onClick={() => setFiltersOpen(true)}
                        aria-expanded={filtersOpen}
                        className="md:hidden shrink-0 border rounded-full px-4 py-1 text-sm tracking-widest"
                    >
                        FILTER{filterCount > 0 && ` (${filterCount})`}
                    </button>
                )}
            </div>

            {categoryNotFound ? (
                <p className="tracking-wider text-gray-500">
                    This category no longer exists. <Link to="/products" className="underline">View all products</Link>
                </p>
            ) : loadingProducts ? (
                <LoadingState label="Loading products" />
            ) : loadFailed ? (
                <ErrorState message="We couldn't load the products." onRetry={() => setAttempt((n) => n + 1)} />
            ) : products.length === 0 ? (
                <p className="tracking-wider text-gray-500">
                    {isNewArrivals ? "No new arrivals yet." : "No products in this category yet."}
                </p>
            ) : visibleProducts.length === 0 ? (
                <div className="flex flex-col items-start gap-3">
                    <p className="tracking-wider text-gray-500">No products match these filters.</p>
                    <button
                        onClick={clearFilters}
                        className="border border-black rounded-full px-6 py-1.5 tracking-wider hover:bg-black hover:text-white transition"
                    >
                        Clear filters
                    </button>
                </div>
            ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {visibleProducts.map((product) => (
                    <ProductCard key={product.product_id} product={product} />
                ))}
            </div>
            )}
            </div>

        </div>

        <Drawer
            open={filtersOpen}
            onClose={closeFilters}
            title="FILTER"
            footer={
                <button onClick={closeFilters} className="w-full bg-black text-white rounded-full py-2 tracking-widest">
                    SHOW {visibleProducts.length} {visibleProducts.length === 1 ? "ITEM" : "ITEMS"}
                </button>
            }
        >
            <ProductFilters
                inDrawer
                filters={filters}
                sizeOptions={sizeOptions}
                colorOptions={colorOptions}
                canClear={hasActiveFilters(filters, defaultSort)}
                onChange={setFilters}
                onClear={clearFilters}
            />
        </Drawer>

        </main>
        </>
    );
}