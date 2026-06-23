import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

console.log("DEBUG: Landing page component loaded");


function Landing() {

    return (
        <>
        {/* Header */}
        <div className="flex flex-col justify-center items-center gap-4 p-5">
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
        
        {/* Hero Section */}
        <div className="flex flex-col justify-center h-screen p-10 gap-10 bg-gray-500">
            <h2 className="text-4xl">Vintage clothing for cheap.</h2>

            <div className="flex flex-row gap-6">
                <a href="/products"><span className="bg-black text-white pl-[40px] pr-[40px] pt-[10px] pb-[10px] rounded-full">Shop now</span></a>
                <a href=""><span className="bg-white text-black pl-[40px] pr-[40px] pt-[10px] pb-[10px] rounded-full">Find next event</span></a>
            </div>
        </div>

        <div>
            <h2>New Arrivals</h2>
        </div>
        </>
    );
}

export default Landing;