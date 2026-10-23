import { useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import { store } from "../config/store";

interface NotFoundProps {
    heading?: string;
    message?: string;
}

// Unknown addresses, and product pages for products that don't exist
export default function NotFound({
    heading = "PAGE NOT FOUND",
    message = "We couldn't find the page you were looking for.",
}: NotFoundProps) {
    useEffect(() => {
        document.title = `Not found | ${store.name}`;
        return () => { document.title = store.name; };
    }, []);

    return (
        <>
        <Navbar />

        <main className="flex flex-col items-center gap-6 px-4 py-20 text-center">
            <h2 className="text-2xl md:text-4xl tracking-widest">{heading}</h2>
            <p className="tracking-wider text-gray-500">{message}</p>
            <div className="flex flex-wrap justify-center gap-4">
                <Link to="/" className="border border-black rounded-full px-8 py-2 tracking-wider hover:bg-black hover:text-white transition">
                    Home
                </Link>
                <Link to="/products" className="bg-black text-white rounded-full px-8 py-2 tracking-wider hover:bg-gray-800 transition">
                    Shop all products
                </Link>
            </div>
        </main>
        </>
    );
}
