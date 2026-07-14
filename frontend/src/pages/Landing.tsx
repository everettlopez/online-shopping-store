import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";
import heroBg from "../assets/pexels-arturoaez225-13662505.jpg";

console.log("DEBUG: Landing page component loaded");

type Product = {
  product_id: number;
  name: string;
  price: number;
  image_url: string;
  description?: string;
  category_id?: number;
  stock_quantity?: number;
};

type ProductResponse = {
    metadata: {
        count: number;
        sort?: string | null;
    };
    products: Product[];
};



function Landing() {

    const [newArrivals, setNewArrivals] = useState<Product[]>([]);


    useEffect(() => {
        async function fetchNewArrivals() {
            const res = await fetch("/api/products?category=1");
            const data: ProductResponse = await res.json();
            setNewArrivals(data.products);
        }

        fetchNewArrivals();
        }, []);




    return (
        <>
        {/* Header */}
        <div className="relative flex flex-col justify-center items-center gap-4 p-5">

            {/* Right-side icons */}
            <div className="absolute right-5 top-5 flex items-center gap-6 text-2xl">
                <Link to="/account" className="hover:text-gray-600 transition">
                    <i className="fa-regular fa-user"></i>
                </Link>

                <Link to="/cart" className="hover:text-gray-600 transition">
                    <i className="fa-solid fa-bag-shopping"></i>
                </Link>
            </div>

            {/* Logo */}
            <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

            {/* Navigation */}
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

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-10 mt-10 max-w-7xl mx-auto">
                {/* Map your products here */}
                {newArrivals.map((p) => (
                <div 
                    key={p.product_id} 
                    className="flex flex-col items-center bg-white rounded-xl shadow hover:shadow-xl transition p-4"
                >
                    <img 
                    src={p.image_url} 
                    alt={p.name} 
                    className="w-full h-64 object-cover rounded-lg"
                    />

                    <h3 className="mt-4 text-lg font-semibold">{p.name}</h3>
                    <p className="text-gray-600">${p.price}</p>
                </div>
                ))}
            </div>
        </div>

        </>
    );
}

export default Landing;