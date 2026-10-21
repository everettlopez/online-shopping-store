import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import { useCategories } from "../context/CategoriesContext";
import UserProductDetailModal from "../components/products/UserProductDetailModal";
import Navbar from "../components/Navbar";

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
    const products = loadingProducts ? [] : loaded.products;

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
            <div className="border flex flex-col p-10">
                <h2>Filter</h2>
            </div>

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
            ) : (
            <div className="grid grid-cols-4 gap-3">
                {products.map((product) => {
                    return (
                    <div onClick={() => {
                        setIsProductDetailModalOpen(true); 
                        setSelectedProduct(product);
                        }} key={product.product_id} className="border flex flex-col gap-2 h-auto hover:bg-gray-100 rounded-2xl p-2 cursor-pointer">
                        <img src={product.thumbnail} className="h-60 object-cover border rounded-2xl"/>
                        <div className="flex flex-col gap-1">
                            <p className="text-lg leading-tight tracking-wider">{product.title.toUpperCase()}</p>
                            <div>
                                <p className="tracking-wider text-gray-500">${product.price.toFixed(2)}</p>
                                <p className="tracking-wider text-gray-500">Size: {product.size}</p>
                            </div>
                        </div>
                    </div>
                    );
                })}
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