import heroBg from "../assets/pexels-arturoaez225-13662505.jpg";
import model_1 from "../assets/model_1.jpg";
import Navbar from "../components/Navbar";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axiosClient from "../api/axiosClient";
import ProductCard from "../components/products/ProductCard";

interface NewArrival {
    product_id: number;
    title: string;
    price: number;
    size?: string | null;
    thumbnail?: string | null;
}

function Landing() {

    const navigate = useNavigate();

    // null until loaded, so the "coming soon" message doesn't flash before the fetch finishes
    const [newArrivals, setNewArrivals] = useState<NewArrival[] | null>(null);

    // Fetch the newest products for the New Arrivals section
    useEffect(() => {
        let cancelled = false;
        axiosClient.get("/products/active", { params: { sort: "newest", limit: 8 } })
            .then((response) => { if (!cancelled) setNewArrivals(response.data); })
            .catch((err) => {
                console.error("Failed to fetch new arrivals: ", err);
                if (!cancelled) setNewArrivals([]);
            });

        return () => { cancelled = true; };
    }, []);

    return (
        <>
        {/* Header */}
        <Navbar />

        
        {/* Hero Section */}
        <div 
            className="flex flex-col justify-center h-screen p-10 gap-10 bg-cover bg-center"
            style={{ backgroundImage: `url(${heroBg})` }}
        >
            <h2 className="text-[4rem] leading-[1.1] font-medium tracking-tight text-white">
            vintage clothing. right in your hands.
            </h2>


            <div className="flex flex-row gap-6">
                <a href="/products">
                    <span className="bg-black text-white px-10 py-3 rounded-full">Shop now</span>
                </a>
                <a href="">
                    <span className="bg-white text-black px-10 py-3 rounded-full">Find next event</span>
                </a>
            </div>
        </div>

        {/* New Arrival Section */}
        <div className="mt-10 px-6 py-10">
            <h2 className="text-[4rem] leading-[1.1] font-medium tracking-tight text-black p-2 text-center">
                NEW ARRIVALS
            </h2>

            {newArrivals !== null && newArrivals.length === 0 ? (
                <p className="text-center tracking-wider text-gray-500 mt-10">New arrivals coming soon.</p>
            ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-10 mt-10 max-w-7xl mx-auto">
                {newArrivals?.map((product) => (
                    <ProductCard
                        key={product.product_id}
                        product={product}
                        onClick={() => navigate("/products?sort=newest")}
                    />
                ))}
            </div>
            )}

            {newArrivals !== null && newArrivals.length > 0 && (
                <div className="flex justify-center mt-10">
                    <Link to="/products?sort=newest" className="border border-black rounded-full px-10 py-3 tracking-wider hover:bg-black hover:text-white transition">
                        View all
                    </Link>
                </div>
            )}
        </div>

        <div className="flex flex-col justify-center h-[200px] p-10 gap-10 bg-cover bg-center"
            style={{ backgroundImage: `url(${model_1})`, backgroundAttachment: "fixed"}}>
        </div>

        {/* CONTACT SECTION */}
        <div className="bg-gray-100 py-16 px-6">
        <div className="max-w-2xl mx-auto bg-white rounded-[12px] shadow-md p-10">

            <h2 className="text-4xl font-semibold tracking-tight text-center mb-10">
            CONTACT US
            </h2>

            <form className="flex flex-col gap-6">

            {/* First Name */}
            <div className="flex flex-col border border-gray-300 rounded-[10px] p-4 bg-white">
                <label className="text-sm text-gray-500">First Name</label>
                <input
                placeholder="Erick"
                className="h-[36px] text-[18px] border-none focus:outline-none focus:ring-0"
                />
            </div>

            {/* Last Name */}
            <div className="flex flex-col border border-gray-300 rounded-[10px] p-4 bg-white">
                <label className="text-sm text-gray-500">Last Name</label>
                <input
                placeholder="Friesland"
                className="h-[36px] text-[18px] border-none focus:outline-none focus:ring-0"
                />
            </div>

            {/* Email */}
            <div className="flex flex-col border border-gray-300 rounded-[10px] p-4 bg-white">
                <label className="text-sm text-gray-500">Email</label>
                <input
                placeholder="supercooldude@gmail.com"
                className="h-[36px] text-[18px] border-none focus:outline-none focus:ring-0"
                />
            </div>

            {/* Category Dropdown */}
            <div className="flex flex-col border border-gray-300 rounded-[10px] p-4 bg-white relative">
                <label className="text-sm text-gray-500">Reason for Contact</label>

                <select
                className="
                    rounded-[8px]
                    py-2
                    px-3
                    bg-white
                    text-gray-700
                    focus:outline-none
                    focus:ring-0
                    appearance-none
                    pr-8
                    text-[18px]
                "
                >
                <option value={0} disabled>Select a category</option>
                <option>Trades and Swaps</option>
                <option>Bulk Purchasing</option>
                </select>

                {/* Custom arrow */}
                <div className="pointer-events-none absolute right-6 bottom-[22px] text-gray-400">
                ▼
                </div>
            </div>

            {/* Submit Button */}
            <button
                className="
                bg-black
                text-white
                py-3
                rounded-full
                text-lg
                tracking-wide
                hover:bg-gray-800
                transition
                "
            >
                Submit
            </button>

            </form>
        </div>
        </div>

        </>
    );
}

export default Landing;