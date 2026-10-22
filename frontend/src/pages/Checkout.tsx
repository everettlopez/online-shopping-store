import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Link } from "react-router-dom";
import backIcon from "../assets/backIcon.svg";
import axiosClient from "../api/axiosClient";
import Navbar from "../components/Navbar";

interface CheckoutProduct {
  title: string;
  price: number;
  size?: string;
  thumbnail?: string;
  images?: string[];
}

interface CheckoutCartItem {
  cart_item_id: number;
  quantity: number;
  product: CheckoutProduct | null;
}

interface ShippingRates {
  flat_rate: number;
  free_shipping_threshold: number;
}

export default function Checkout() {
  const location = useLocation();
  const [checkoutError, setCheckoutError] = useState("");
  const [shippingRates, setShippingRates] = useState<ShippingRates | null>(null);

  useEffect(() => {
    axiosClient.get("/payments/shipping")
      .then((res) => setShippingRates(res.data))
      .catch((err) => console.error("Failed to load shipping rates:", err));
  }, []);

  async function handlePlaceOrder() {
    setCheckoutError("");
    try {
        // The server works out the amount from the cart; only the addresses are sent
        const response = await axiosClient.post("/payments/create-checkout-session", {
        shipping_address_id: shippingAddress.address_id,
        billing_address_id: billingAddress.address_id
        });

        window.location.href = response.data.checkoutUrl;

    } catch (err: any) {
        console.error("Failed to start checkout:", err);
        setCheckoutError(err.response?.data?.detail ?? "Something went wrong starting checkout. Please try again.");
    }
    }




  const { shippingAddress, billingAddress, cart } = location.state || {};

  // In cents, so the sums don't pick up float rounding errors
  const subtotalCents = cart.items.reduce((sum: number, item: CheckoutCartItem) => {
    return sum + item.quantity * Math.round((item.product?.price ?? 0) * 100);
  }, 0);

  // Mirrors the server's rule: flat rate, free once the items reach the threshold
  const shippingCents = shippingRates === null
    ? null
    : subtotalCents >= Math.round(shippingRates.free_shipping_threshold * 100) ? 0 : Math.round(shippingRates.flat_rate * 100);

  const dollars = (cents: number) => `$${(cents / 100).toFixed(2)}`;

  return (
    <>
    {/* Header */}
    <Navbar />

    <div className="flex text-center items-center gap-3 px-10 py-4">
        <Link to="/cart" className="flex items-center gap-3">
            <img src={backIcon} className="w-8 h-8"/>
            <p className="tracking-wider text-lg">BACK TO CART</p>
        </Link>
    </div>

    <div className="flex justify-evenly">
        {/* Left Column */}
        <div className="flex flex-col">
            
            <div className="flex flex-col p-3 gap-2">
                {cart.items.map((item: CheckoutCartItem) => {
                    const mainImage = item.product?.thumbnail || item.product?.images?.[0];

                    return (
                        <div 
                            key={item.cart_item_id} 
                            className="flex justify-center items-center border mx-auto p-5 rounded-[10px] gap-5 w-70">
                                
                                <img src={mainImage} className="w-40 h-40 object-cover"/>

                                <div className="flex flex-col">
                                    <h2 className="w-60 text-xl">{item.product?.title}</h2>
                                    <p>{item.product?.size}</p>
                                    <p>${item.product?.price.toFixed(2)}</p>
                                </div>
                        </div>
                    );
                })}
            </div>

        </div>

        {/* Right Column */}
        <div className="flex flex-col">
            <div className="flex flex-col p-3 gap-2">
                <div className="flex flex-col justify-center items-center border mx-auto p-5 rounded-[10px] gap-5 w-[500px]">
                    <h1 className="text-xl">CHECKOUT</h1>

                    <div className="flex flex-col w-full gap-1 px-10">
                        <div className="flex justify-between">
                            <p>Subtotal</p>
                            <p>{dollars(subtotalCents)}</p>
                        </div>
                        <div className="flex justify-between">
                            <p>Shipping</p>
                            <p>{shippingCents === null ? "Calculated at payment" : shippingCents === 0 ? "Free" : dollars(shippingCents)}</p>
                        </div>
                        <div className="flex justify-between text-gray-500">
                            <p>Sales tax</p>
                            <p>Calculated at payment</p>
                        </div>
                        <div className="flex justify-between text-lg pt-2 border-t">
                            <p>Estimated total</p>
                            <p>{dollars(subtotalCents + (shippingCents ?? 0))} + tax</p>
                        </div>
                        {shippingRates && shippingCents !== 0 && (
                            <p className="text-sm text-gray-500 text-center pt-2">
                                Free shipping on orders of ${shippingRates.free_shipping_threshold.toFixed(2)} or more
                            </p>
                        )}
                    </div>

                    {checkoutError && <p className="text-center text-sm text-red-600">{checkoutError}</p>}

                    <button
                        onClick={handlePlaceOrder}
                        className="border py-2 px-5 rounded-[10px] hover:bg-gray-300">Place Order</button>
                </div>
            </div>
        </div>
    </div>
    </>
  );
}
