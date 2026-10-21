import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import { useCategories } from "../context/CategoriesContext";
import UserProductDetailModal from "../components/products/UserProductDetailModal";
import Navbar from "../components/Navbar";
import ProductCard from "../components/products/ProductCard";
import ProductFilters from "../components/products/ProductFilters";
import { applyProductFilters, defaultProductFilters, filterOptions, hasActiveFilters, type ProductFilterState } from "../utils/productFilters";

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

interface CartItem {
    cart_item_id: number;
    product_id: number;
    quantity: number;
    product: Product | null;
}

interface Cart {
    cart_id: number;
    user_id: number;
    items: CartItem[];
}

export default function Products() {

    // Products are tagged with the URL query they were fetched for, so switching
    // categories never shows the previous category's products under the new heading
    const [loaded, setLoaded] = useState<{ key: string; products: Product[] } | null>(null);
    const [cart, setCart] = useState<Cart | null>(null);
    const [isProductDetailModalOpen, setIsProductDetailModalOpen] = useState(false);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

    const [searchParams] = useSearchParams();
    const { categories, loading: loadingCategories } = useCategories();

    const categoryParam = searchParams.get("category");
    const isNewArrivals = searchParams.get("sort") === "newest";
    const categoryId = categoryParam !== null && /^\d+$/.test(categoryParam) ? Number(categoryParam) : null;
    const currentCategory = categories.find((category) => category.category_id === categoryId);
    const categoryNotFound = categoryParam !== null && !loadingCategories && !currentCategory;

    const productsKey = `${categoryId ?? "all"}|${isNewArrivals ? "newest" : ""}`;
    const loadingProducts = loaded?.key !== productsKey;
    const products = useMemo(() => (loaded?.key === productsKey ? loaded.products : []), [loaded, productsKey]);

    // Filters belong to the URL query they were set on, so switching categories resets them
    const defaultSort = isNewArrivals ? "newest" : "featured";
    const [filterState, setFilterState] = useState<{ key: string; filters: ProductFilterState } | null>(null);
    const filters = filterState?.key === productsKey ? filterState.filters : defaultProductFilters(defaultSort);
    const setFilters = (next: ProductFilterState) => setFilterState({ key: productsKey, filters: next });

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
                if (!cancelled) setLoaded({ key: productsKey, products: [] });
            });

        return () => { cancelled = true; };
    }, [categoryId, categoryParam, isNewArrivals, productsKey]);

    // Fetch Cart
    useEffect(() => {
        axiosClient.get("/cart")
            .then((response) => setCart(response.data))
            .catch((err) => console.error("Failed to fetch cart: ", err));
    }, []);



    return (
        <>
        {/* Header */}
        <Navbar />

        {/* Main */}
        <div className="flex gap-2 p-8">
            
            {/* Filter Section */}
            <ProductFilters
                filters={filters}
                sizeOptions={sizeOptions}
                colorOptions={colorOptions}
                canClear={hasActiveFilters(filters, defaultSort)}
                onChange={setFilters}
                onClear={() => setFilters(defaultProductFilters(defaultSort))}
            />

            {/* Products Grid */}
            <div className="flex flex-col gap-4 flex-1">
            <h2 className="text-2xl tracking-widest">{categoryNotFound ? "CATEGORY NOT FOUND" : heading}</h2>

            {categoryNotFound ? (
                <p className="tracking-wider text-gray-500">
                    This category no longer exists. <Link to="/products" className="underline">View all products</Link>
                </p>
            ) : !loadingProducts && products.length === 0 ? (
                <p className="tracking-wider text-gray-500">
                    {isNewArrivals ? "No new arrivals yet." : "No products in this category yet."}
                </p>
            ) : !loadingProducts && visibleProducts.length === 0 ? (
                <p className="tracking-wider text-gray-500">No products match these filters.</p>
            ) : (
            <div className="grid grid-cols-4 gap-3">
                {visibleProducts.map((product) => (
                    <ProductCard
                        key={product.product_id}
                        product={product}
                        onClick={() => {
                            setIsProductDetailModalOpen(true);
                            setSelectedProduct(product);
                        }}
                    />
                ))}
            </div>
            )}
            </div>

        </div>

        <UserProductDetailModal 
            isOpen={isProductDetailModalOpen}
            product={selectedProduct}
            cart={cart}
            onClose={() => setIsProductDetailModalOpen(false)}/>

        </>
    );
}