import { useLocation, useNavigate } from "react-router-dom";
import { useSearchParams, Link } from "react-router-dom";
import backIcon from "../assets/backIcon.svg";
import axiosClient from "../api/axiosClient";

export default function Checkout() {
  const location = useLocation();
  const navigate = useNavigate();

  async function handlePlaceOrder() {
    try {
        const response = await axiosClient.post("/payments/create-payment-intent", {
        total_amount: cartTotal,
        shipping_address_id: shippingAddress.address_id,
        billing_address_id: billingAddress.address_id
        });

        const clientSecret = response.data.clientSecret;

        navigate("/payments", {
        state: {
            clientSecret,
            cart,
            shippingAddress,
            billingAddress
        }
        });
    } catch (err) {
        console.error("Failed to start payment:", err);
    }
    }



  const { shippingAddress, billingAddress, cart } = location.state || {};

  const cartTotal = cart.items.reduce((sum, item) => {
    return sum + item.quantity * item.product.price;
  }, 0);

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

                    <div className="flex w-full justify-evenly">
                        <p>Total: </p>
                        <p>${cartTotal.toFixed(2)}</p>
                    </div>

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
