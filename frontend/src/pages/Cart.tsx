import { useState } from "react";
import axiosClient from "../api/axiosClient";
import { useAuth } from "../context/useAuth";
import { useCart } from "../context/useCart";
import { cartErrorMessage, MAX_CART_QUANTITY } from "../context/guestCart";
import type { CartLine } from "../api/cart";

import { Link, useNavigate } from "react-router-dom";
import AddressModal from "../components/AddressModal";
import Navbar from "../components/Navbar";
import { EmptyState, LoadingState } from "../components/Status";

interface Address {
  address_id: number;
  user_id: number;
  full_name: string;
  phone?: string | null;
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postal_code: string;
  county?: string;
  address_type: string;
  created_at: string; // or Date if you convert it
}


// Why a cart line can't be bought as it is, or null when it can
function lineProblem(item: CartLine): string | null {
    if (!item.product) return null;
    if (!item.product.is_active) return "No longer available";
    if (item.product.stock_quantity <= 0) return "Sold out";
    if (item.quantity > item.product.stock_quantity) return `Only ${item.product.stock_quantity} left`;
    return null;
}


export default function Cart() {

    const { isAuthenticated } = useAuth();
    const { items, loading, updateQuantity, remove } = useCart();
    const navigate = useNavigate();
    const [error, setError] = useState("");

    // Address Modal (logged-in shoppers check out with their saved addresses)
    const [isAddressModalOpen, setIsAddressModalOpen] = useState(false);
    const [addresses, setAddresses] = useState<Address[]>([]);

    async function fetchAddresses() {
        try {
            // Any saved address can be used for shipping or billing
            const res = await axiosClient.get("/addresses/");
            setAddresses(res.data);
        } catch (err) {
            console.error("Failed to load addresses:", err);
        }
    }

    if (loading) return <><Navbar /><LoadingState label="Loading your cart" page /></>;

    // Checkout would refuse these lines, so say so here and hold the button until they're fixed
    const unavailable = items.some((item) => lineProblem(item) !== null);

    // In cents, so the sum doesn't pick up float rounding errors
    const cartTotalCents = items.reduce((sum, item) => {
        return sum + Math.round((item.product?.price ?? 0) * 100) * item.quantity;
    }, 0);

    async function change(action: () => Promise<void>) {
        setError("");
        try {
            await action();
        } catch (err) {
            setError(cartErrorMessage(err, "We couldn't update your cart. Please try again."));
        }
    }

    function handleCheckout() {
        if (isAuthenticated) {
            fetchAddresses();
            setIsAddressModalOpen(true);
        } else {
            // Guests enter their email and addresses on Stripe's payment page
            navigate("/checkout");
        }
    }

    return (
        <>
        {/* Header */}
        <Navbar />
        <main>

        <nav aria-label="Breadcrumb" className="flex text-center items-center gap-3 px-4 sm:px-10 py-4 text-gray-500">
            <Link to="/" className="text-sm tracking-wider">HOME</Link>
            <span>/</span>
            <Link to="/products" className="text-sm tracking-wider">PRODUCTS</Link>
            <span>/</span>
            <Link to="/cart" aria-current="page" className="text-sm tracking-wider">CART</Link>
        </nav>

        <div className="flex flex-col">
            <h1 className="text-center text-3xl tracking-widest text-gray-500 border-y py-4">CART</h1>

            {items.length === 0 && (
                <EmptyState title="Your cart is empty" message="Find something you'll love." action={{ to: "/products", label: "Keep shopping" }} />
            )}

            <div className="flex flex-col p-3 gap-2">

                {items.map((item) => {
                    const mainImage = item.product?.thumbnail || item.product?.images?.[0];
                    const maxQuantity = Math.min(MAX_CART_QUANTITY, item.product?.stock_quantity ?? MAX_CART_QUANTITY);
                    const problem = lineProblem(item);

                    return (
                        <div
                            key={item.product_id}
                            className="flex items-center border w-full max-w-xl mx-auto p-3 sm:p-5 rounded-[10px] gap-4 sm:gap-5">

                                <img src={mainImage} alt={item.product?.title ?? ""} loading="lazy" className="w-24 h-24 sm:w-40 sm:h-40 object-cover shrink-0"/>

                                <div className="flex flex-col gap-1 min-w-0 flex-1">
                                    <h2 className="text-lg sm:text-xl break-words">{item.product?.title}</h2>
                                    <p>{item.product?.size}</p>
                                    <p>${item.product?.price.toFixed(2)}</p>
                                    {problem && <p className="text-sm text-red-600">{problem}</p>}

                                    <div className="flex items-center gap-3">
                                        <button
                                            onClick={() => change(() => updateQuantity(item.product_id, item.quantity - 1))}
                                            disabled={item.quantity <= 1}
                                            aria-label="Decrease quantity"
                                            className="border w-7 rounded-sm disabled:opacity-40">−</button>
                                        <span aria-label={`Quantity ${item.quantity}`}>{item.quantity}</span>
                                        <button
                                            onClick={() => change(() => updateQuantity(item.product_id, item.quantity + 1))}
                                            disabled={item.quantity >= maxQuantity}
                                            aria-label="Increase quantity"
                                            className="border w-7 rounded-sm disabled:opacity-40">+</button>
                                    </div>

                                    <button
                                        onClick={() => change(() => remove(item.product_id))}
                                        className="flex w-fit underline underline-offset-4 hover:text-gray-600">Remove</button>
                                </div>
                        </div>
                    );
                })}

            </div>

        </div>

        {items.length > 0 && (
        <div className="flex flex-col mx-auto justify-center px-4 py-6 gap-6 max-w-xl">

        {error && <p role="alert" className="text-center text-sm text-red-600">{error}</p>}

        {/* Cart Total */}
        <div className="flex justify-center gap-20 text-lg">
            <p>Total:</p>
            <p>${(cartTotalCents / 100).toFixed(2)}</p>
        </div>

        {/* Checkout Button */}
        <button
            onClick={handleCheckout}
            disabled={unavailable}
            className="py-2 px-3 bg-black text-white mx-auto rounded-[10px] text-lg disabled:opacity-40"
        >
            Checkout
        </button>

        {unavailable && (
            <p className="text-center text-sm text-red-600">
                Some items can't be bought right now. Remove them or lower their quantity to check out.
            </p>
        )}

        {!isAuthenticated && (
            <p className="text-center text-sm text-gray-500">
                No account needed. Have one?{" "}
                <Link to="/login" state={{ from: "/cart" }} className="underline">Log in</Link> to use your saved addresses.
            </p>
        )}
        </div>
        )}


        <AddressModal
            isOpen={isAddressModalOpen}
            onClose={() => setIsAddressModalOpen(false)}
            onSaved={({ shipping, billing }) => {
                navigate("/checkout", {
                state: { shippingAddress: shipping, billingAddress: billing }
                });
            }}
            addresses={addresses}
            />



        </main>
        </>
    );
}
