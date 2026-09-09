import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

import { useSearchParams, Link } from "react-router-dom";

import { useNavigate } from "react-router-dom";
import ProductModal from "../components/ProductModal";
import ProductDetailModal from "../components/ProductDetailModal";
import axiosClient from "../api/axiosClient";

console.log("DEBUG: Landing page component loaded");

type Product = {
    product_id: number;
    category_id: number;
    name: string;
    description?: string;
    price: number;
    size?: string;
    color?: string;
    image_url?: string;
    images?: string[];
    stock_quantity: number;
    is_active: boolean;
};

type Category = {
    category_id: number;
    name: string;
    description?: string;
}

type ProductResponse = {
    metadata: {
        count: number;
        sort?: string | null;
    };
    products: Product[];
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
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { user } = useAuth();

    const [isModalOpen, setIsModalOpen] = useState(false);

    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
    const [detailProduct, setDetailProduct] = useState<Product | null>(null);
    const [isDetailOpen, setIsDetailOpen] = useState(false);

    const [cart, setCart] = useState<Cart | null>(null);

    function openDetail(product: Product) {
        setDetailProduct(product);
        setIsDetailOpen(true);
    }

    function closeDetail() {
        setIsDetailOpen(isDetailOpen);
        setDetailProduct(null);
    }


    

    function openEditModal(product: Product) {
        setSelectedProduct(product);
        setIsModalOpen(true);
    }

    function updateFilter(key: string, value: string | null) {
        const params = new URLSearchParams(window.location.search);

        if (value === null) {
            params.delete(key);
        } else {
            params.set(key, value);
        }

        navigate(`/products?${params.toString()}`);
    };

    function isPriceActive(range: string) {
        const { min, max } = priceMap[range];
        return (
            (min ? String(min) === price_min : !price_min) &&
            (max ? String(max) === price_max : !price_max)
        );
    }


    const category = searchParams.get("category");
    const size = searchParams.get("size");
    const color = searchParams.get("color");
    const price_min = searchParams.get("price_min");
    const price_max = searchParams.get("price_max");

    const [metadata, setMetadata] = useState<{ count: number; sort?: string | null }>({
        count: 0,
        sort: null
    });




    const [products, setProducts] = useState<Product[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);

    const priceMap: Record<string, { min?: number; max?: number }> = {
        "Under $25": { max: 25 },
        "$25 – $50": { min: 25, max: 50 },
        "$50 – $100": { min: 50, max: 100 },
        "$100 – $200": { min: 100, max: 200 },
        "$200+": { min: 200 },
    };


    useEffect(() => {
        const load = async () => {
            const params = new URLSearchParams();

            if (category && category !== "all") params.set("category", category);
            if (size) params.set("size", size);
            if (color) params.set("color", color);
            if (price_min) params.set("price_min", price_min);
            if (price_max) params.set("price_max", price_max);

            const url = `/api/products?${params.toString()}`;

            const res = await fetch(url);
            const data: ProductResponse = await res.json();
            setProducts(data.products);
            setMetadata(data.metadata);
        };

        load();
    }, [category, size, color, price_min, price_max]);


    useEffect(() => {
        const loadCategories = async () => {
            const res = await fetch("/api/categories");
            const data = await res.json();
            setCategories(data.categories);
        };

        loadCategories();
    }, []);

    const currentCategory = categories.find(
        (c) => c.category_id === Number(category)
    );

    const { isAuthenticated } = useAuth();
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isAuthenticated) {
            setCart(null);
            setLoading(false);
            return;
        }

        const fetchCart = async () => {
            try {
                const res = await axiosClient.get("/cart", {withCredentials: true});
                setCart(res.data);
            } catch (err){
                console.error("Failed to load cart:", err);
                setCart(null)
            } finally {
                setLoading(false);
            }
        };

        fetchCart();

    }, [isAuthenticated]);

    async function handleAddToCart(product: Product)
    {
        try
        {
            const response = await axiosClient.post("/cart/items", {
                product_id: product.product_id,
                quantity: 1
            }, {withCredentials: true});

            const newItem: CartItem = response.data;

            setCart((prev) => ({
                ...prev!,
                items: [...prev!.items, newItem]
            }));
        }
        catch (err)
        {
            console.error("Failed to add item: ", err);
        }
    }


    return (
        <>
        {/* Header */}
        <div className="flex flex-col justify-center items-center gap-4 p-5">

            {/* Right-side icons */}
            <div className="absolute right-5 top-5 flex items-center gap-6 text-2xl">
                <Link to="/account" className="hover:text-gray-600 transition">
                    <i className="fa-regular fa-user"></i>
                </Link>

                <Link to="/cart" className="hover:text-gray-600 transition">
                    <i className="fa-solid fa-bag-shopping"></i>
                </Link>
            </div>

            <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

            <nav className="flex gap-12">
                <Link to="/"><p className="text-base font-normal tracking-widest">EVENTS</p></Link>
                <Link to="/products?category=1"><p className="text-base font-normal tracking-widest">NEW ARRIVALS</p></Link>
                <Link to="/products?category=2"><p className="text-base font-normal tracking-widest">WOMEN</p></Link>
                <Link to="/products?category=3"><p className="text-base font-normal tracking-widest">MEN</p></Link>
                <Link to="/products?category=4"><p className="text-base font-normal tracking-widest">BRANDS</p></Link>
                <Link to="/products?category=5"><p className="text-base font-normal tracking-widest">ACCESSORIES</p></Link>
                <Link to="/products?category=6"><p className="text-base font-normal tracking-widest">JEWELERY</p></Link>
            </nav>
        </div>

        <div className="flex text-center items-center gap-3 px-10 py-4 text-gray-400 ">
            <Link to="/" className="text-sm tracking-wider">HOME</Link>
            <span>/</span>
            <Link to="/products" className="text-sm tracking-wider">PRODUCTS</Link>
            <span>/</span>
            <Link to={`/products?category=${currentCategory ? currentCategory.category_id : ""}`} className="text-sm tracking-wider">
                {currentCategory ? currentCategory.name : "ALL PRODUCTS"}
            </Link>
        </div>

        {/* Cateogry Section Title */}
        <div className="flex flex-col justify-center items-center gap-4 p-5">
            <h2 className="text-3xl font-normal tracking-widest">
                {currentCategory ? currentCategory.name : "ALL PRODUCTS"}
            </h2>
        </div>

        <div className="flex text-center justify-center text-lg tracking-wider text-gray-400 border py-4">{metadata.count} PRODUCTS</div>

        <div className="flex gap-6">

            {/* Filter Section */}
            <div className="flex flex-col p-5 gap-6">

                {/* SIZE – debug version */}
                <div className="flex flex-col space-y-2">
                    <p className="text-sm font-semibold">SIZE</p>

                    <div className="flex gap-2">
                        {["XS", "S", "M", "L", "XL"].map((size) => (
                        <button
                            key={size}
                            onClick={() =>
                            updateFilter("size", size === searchParams.get("size") ? null : size)
                            }
                            className={
                            "inline-flex items-center justify-center h-10 w-10 border p-0 text-sm " +
                            (searchParams.get("size") === size
                                ? "bg-black text-white border-black"
                                : "border-gray-300 hover:bg-gray-100")
                            }
                        >
                            {size}
                        </button>
                        ))}
                    </div>
                </div>




                {/* COLOR */}
                <div className="flex flex-col gap-3">
                    <p className="text-xl tracking-wider">COLOR</p>

                    <details className="w-full">
                        <summary className="cursor-pointer border border-gray-300 px-4 py-3 tracking-wide">
                            Select Color
                        </summary>

                        <div className="flex flex-col border border-gray-300 border-t-0">
                            {["Black", "White", "Red", "Blue", "Green"].map((color) => (
                                <button
                                    key={color}
                                    onClick={() =>
                                        updateFilter("color", color === searchParams.get("color") ? null : color)
                                    }
                                    className={
                                        "w-full text-left px-4 py-3 tracking-wide " +
                                        (searchParams.get("color") === color
                                            ? "bg-black text-white"
                                            : "hover:bg-gray-100")
                                    }
                                >
                                    {color}
                                </button>
                            ))}
                        </div>
                    </details>
                </div>

                {/* PRICE */}
                <div className="flex flex-col gap-3">
                    <p className="text-xl tracking-wider">PRICE</p>

                    <details className="w-full">
                        <summary className="cursor-pointer border border-gray-300 px-4 py-3 tracking-wide">
                            Select Price Range
                        </summary>

                        <div className="flex flex-col border border-gray-300 border-t-0">
                            {["Under $25", "$25 – $50", "$50 – $100", "$100 – $200", "$200+"].map((range) => (
                                <button
                                    key={range}
                                    onClick={() => {
                                        const { min, max } = priceMap[range];

                                        if (isPriceActive(range)) {
                                            updateFilter("price_min", null);
                                            updateFilter("price_max", null);
                                        } else {
                                            updateFilter("price_min", min ? String(min) : null);
                                            updateFilter("price_max", max ? String(max) : null);
                                        }
                                    }}
                                    className={
                                        "w-full text-left px-4 py-3 tracking-wide " +
                                        (isPriceActive(range)
                                            ? "bg-black text-white"
                                            : "hover:bg-gray-100")
                                    }
                                >
                                    {range}
                                </button>
                            ))}
                        </div>
                    </details>
                </div>

            </div>

            {/* Product Content */}
            <div className="p-10">
                
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
                    {products.map((p) => (
                        <div key={p.product_id} className="border p-4 rounded-lg shadow cursor-pointer hover:shadow-xl transition" onClick={() => openDetail(p)}>
                            <img src={p.image_url} alt={p.name} className="w-full h-48 object-cover rounded" />
                            <h3 className="mt-4 text-lg font-semibold">{p.name}</h3>
                            <p className="text-gray-600">${p.price}</p>
                            <p className="text-sm text-gray-500">Size: {p.size}</p>
                            <p className="text-sm text-gray-500">Color: {p.color}</p>

                            {user?.is_admin === true ? (
                                <button
                                    onClick={() => openEditModal(p)}
                                    className="mt-4 w-full bg-blue-600 text-white py-2 rounded-full text-sm tracking-wide 
                                            transition-all duration-200 hover:bg-blue-700"
                                >
                                    Edit Product
                                </button>
                            ) : (
                                <div>
                                </div>
                                
                            )}


                            
                        </div>
                    ))}
                </div>

            </div>

        </div>

        <ProductModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            product={selectedProduct}
            />

        <ProductDetailModal
            isOpen={isDetailOpen}
            onClose={closeDetail}
            product={detailProduct}
            cart={cart}
            setCart={setCart}
            handleAddToCart={handleAddToCart}
            />

        </>
    );
}