import defaultHero from "../assets/default-hero.jpg";
import Navbar from "../components/Navbar";
import { store } from "../config/store";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
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
            style={{ backgroundImage: `url(${store.heroImage || defaultHero})` }}
        >
            <h2 className="text-[4rem] leading-[1.1] font-medium tracking-tight text-white">
            {store.heroHeadline}
            </h2>


            <div className="flex flex-row gap-6">
                <Link to="/products">
                    <span className="bg-black text-white px-10 py-3 rounded-full">Shop now</span>
                </Link>
                {store.eventsUrl && (
                    <a href={store.eventsUrl}>
                        <span className="bg-white text-black px-10 py-3 rounded-full">Find next event</span>
                    </a>
                )}
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
                    <ProductCard key={product.product_id} product={product} />
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

        {store.bannerImage && (
            <div className="flex flex-col justify-center h-[200px] p-10 gap-10 bg-cover bg-center"
                style={{ backgroundImage: `url(${store.bannerImage})`, backgroundAttachment: "fixed"}}>
            </div>
        )}

        {/* Contact */}
        <div className="bg-gray-100 py-16 px-6">
            <div className="max-w-2xl mx-auto bg-white rounded-[12px] shadow-md p-10 flex flex-col items-center gap-6 text-center">
                <h2 className="text-4xl font-semibold tracking-tight">QUESTIONS?</h2>
                <p className="text-gray-600">
                    {store.supportEmail
                        ? <>We're happy to help with orders, returns, or anything else. Email us at <a href={`mailto:${store.supportEmail}`} className="underline">{store.supportEmail}</a>.</>
                        : <>We're happy to help with orders, returns, or anything else.</>}
                </p>
                <Link to="/contact" className="bg-black text-white px-10 py-3 rounded-full text-lg tracking-wide hover:bg-gray-800 transition">
                    Contact us
                </Link>
            </div>
        </div>

        </>
    );
}

export default Landing;