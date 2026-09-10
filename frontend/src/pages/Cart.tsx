import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";
import { useAuth } from "../context/AuthContext";

import { useSearchParams, Link } from "react-router-dom";

interface Product {
  product_id: number;
  name: string;
  description?: string;
  price: number;
  size?: string;
  color?: string;
  image_url?: string;
  images?: string[];
  stock_quantity: number;
  is_active: boolean;
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

export default function Cart() {

    const { isAuthenticated } = useAuth();

    const [cart, setCart] = useState<Cart | null>(null);
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

    if (loading) return <p>Loading cart...</p>;
    if(!cart) return <p>No cart found.</p>;

    const cartTotal = cart.items.reduce((sum, item) => {
        const price = item.product?.price ?? 0;
        return sum + price * item.quantity;
    }, 0);

    async function handleRemoveCartItem(item_id: number)
    {
        try
        {
            await axiosClient.delete(`/cart/items/${item_id}`, {
                withCredentials: true,
            });

            setCart((prev) => prev ? {...prev, items: prev.items.filter((i) => i.cart_item_id !== item_id)} : prev);
        }
        catch (err)
        {
            console.error("Failed to remove item: ", err);
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
            <Link to="/cart" className="text-sm tracking-wider">CART</Link>
        </div>

        <div className="flex flex-col">
            <div className="flex text-center justify-center text-3xl tracking-widest text-gray-400 border py-4"><h2>CART</h2></div>

            {cart.items.length === 0 && <p>Your cart is empty.</p>}

            <div className="flex flex-col p-3 gap-2">
                
                {cart.items.map((item) => {
                    const mainImage = item.product?.image_url || item.product?.images?.[0];

                    return (
                        <div 
                            key={item.cart_item_id} 
                            className="flex justify-center items-center border mx-auto p-5 rounded-[10px] gap-5 w-70">
                                
                                <img src={mainImage} className="w-40 h-40 object-cover"/>

                                <div className="flex flex-col">
                                    <h2 className="w-60 text-xl">{item.product?.name}</h2>
                                    <p>{item.product?.size}</p>
                                    <p>${item.product?.price.toFixed(2)}</p>

                                    <button 
                                        onClick={() => handleRemoveCartItem(item.cart_item_id)}
                                        className="flex w-fit hover:bg-gray-400">Remove</button>
                                </div>
                        </div>
                    );
                })};

            </div>

        </div>

        <div className="flex flex-col mx-auto justify-center p-6 gap-6">
            <div className="flex justify-center gap-20 text-lg">
                <p>Total:</p>
                <p>${cartTotal.toFixed(2)}</p>
            </div>

            <button 
                className="py-2 px-3 bg-gray-300 mx-auto rounded-[10px] text-lg">Checkout</button>
        </div>
        </>
    );
}