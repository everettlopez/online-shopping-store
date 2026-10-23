import { useEffect, useState } from "react";
import axios from "axios";
import { Link, useLocation, useParams } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import Navbar from "../components/Navbar";
import { store } from "../config/store";
import { useCart } from "../context/useCart";
import { cartErrorMessage } from "../context/guestCart";
import NotFound from "./NotFound";
import type { Product } from "./Products";

type Loaded =
    | { id: string; status: "found"; product: Product }
    | { id: string; status: "missing" | "error" };

// Product cards pass the grid they were clicked on (with its filters) as `from`;
// only addresses on this site are followed
function backPath(state: unknown): string | null {
    const from = (state as { from?: unknown } | null)?.from;
    return typeof from === "string" && from.startsWith("/") && !from.startsWith("//") && !from.includes("\\") ? from : null;
}

// /products/:id, open to everyone. Inactive and sold-out products still load (old links,
// carts), but can't be added to the cart.
export default function ProductDetail() {
    const { id = "" } = useParams();
    const validId = /^\d+$/.test(id);
    const [loaded, setLoaded] = useState<Loaded | null>(null);

    useEffect(() => {
        if (!validId) return;

        let cancelled = false;
        axiosClient.get<Product>(`/products/${id}`)
            .then((response) => { if (!cancelled) setLoaded({ id, status: "found", product: response.data }); })
            .catch((err) => {
                if (cancelled) return;
                const missing = axios.isAxiosError(err) && err.response?.status === 404;
                if (!missing) console.error("Failed to fetch product: ", err);
                setLoaded({ id, status: missing ? "missing" : "error" });
            });

        return () => { cancelled = true; };
    }, [id, validId]);

    if (!validId || (loaded?.id === id && loaded.status === "missing")) {
        return <NotFound heading="PRODUCT NOT FOUND" message="This product doesn't exist or has been removed." />;
    }

    const current = loaded?.id === id ? loaded : null;

    return (
        <>
        <Navbar />
        <main className="px-4 pb-12 md:px-8">
            {current?.status === "found" ? (
                <ProductView key={current.product.product_id} product={current.product} />
            ) : current?.status === "error" ? (
                <p className="tracking-wider text-gray-500 py-10 text-center">We couldn't load this product. Please refresh to try again.</p>
            ) : (
                <p className="tracking-wider text-gray-500 py-10 text-center">Loading...</p>
            )}
        </main>
        </>
    );
}

function ProductView({ product }: { product: Product }) {
    const location = useLocation();
    const back = backPath(location.state);
    const { items, add } = useCart();
    const [adding, setAdding] = useState(false);
    const [error, setError] = useState("");

    // The thumbnail first, then the other photos, each once
    const photos = [...new Set([product.thumbnail, ...(product.images ?? [])].filter((url): url is string => !!url))];
    const [photo, setPhoto] = useState(0);

    const inCart = items.find((line) => line.product_id === product.product_id)?.quantity ?? 0;
    const unavailable = !product.is_active || product.stock_quantity <= 0;

    useEffect(() => {
        document.title = `${product.title} | ${store.name}`;
        return () => { document.title = store.name; };
    }, [product.title]);

    async function handleAddToCart() {
        setAdding(true);
        setError("");
        try {
            await add(product);
        } catch (err) {
            setError(cartErrorMessage(err, "We couldn't add this to your cart. Please try again."));
        } finally {
            setAdding(false);
        }
    }

    return (
        <div className="flex flex-col gap-4 max-w-6xl mx-auto">
            <Link to={back ?? "/products"} className="self-start text-sm tracking-wider underline underline-offset-4 hover:text-gray-600">
                <i className="fa-solid fa-arrow-left mr-2" aria-hidden="true"></i>
                {back ? "Back" : "All products"}
            </Link>

            <div className="flex flex-col md:flex-row gap-6 md:gap-10">
                {/* Photos */}
                <div className="flex flex-col gap-3 md:w-5/12">
                    {photos.length > 0 ? (
                        <img src={photos[photo]} alt={product.title} className="w-full aspect-[4/5] object-cover border rounded-2xl" />
                    ) : (
                        <div className="w-full aspect-[4/5] border rounded-2xl bg-gray-100" aria-hidden="true" />
                    )}

                    {photos.length > 1 && (
                        <div className="flex gap-2 overflow-x-auto">
                            {photos.map((url, index) => (
                                <button
                                    key={url}
                                    onClick={() => setPhoto(index)}
                                    aria-label={`Photo ${index + 1} of ${photos.length}`}
                                    aria-pressed={index === photo}
                                    className={`shrink-0 w-16 h-20 rounded-lg border-2 overflow-hidden ${index === photo ? "border-black" : "border-transparent"}`}
                                >
                                    <img src={url} alt="" className="w-full h-full object-cover" />
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Details */}
                <div className="flex flex-col gap-6 md:flex-1">
                    <div className="flex flex-col gap-1">
                        <h1 className="text-2xl md:text-4xl tracking-wide break-words">{product.title.toUpperCase()}</h1>
                        <p className="text-gray-500 text-lg py-2">${product.price.toFixed(2)}</p>
                        {product.size && <p className="tracking-wider text-gray-500">Size: {product.size}</p>}
                        {product.color && <p className="tracking-wider text-gray-500">Color: {product.color}</p>}
                    </div>

                    {product.description && <p className="text-lg whitespace-pre-line">{product.description}</p>}

                    <div className="flex flex-col items-start gap-2">
                        {unavailable ? (
                            <p className="tracking-wider text-gray-500">No longer available.</p>
                        ) : (
                            <button
                                onClick={handleAddToCart}
                                disabled={adding}
                                className="bg-black text-white px-10 py-3 rounded-full tracking-wider hover:bg-gray-800 transition disabled:opacity-50"
                            >
                                {adding ? "Adding..." : "Add to Cart"}
                            </button>
                        )}
                        {inCart > 0 && (
                            <p className="text-sm text-gray-500">
                                {inCart} in your cart · <Link to="/cart" className="underline">View cart</Link>
                            </p>
                        )}
                        {error && <p className="text-sm text-red-600">{error}</p>}
                    </div>
                </div>
            </div>
        </div>
    );
}
