import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useSearchParams, Link  } from "react-router-dom";

console.log("DEBUG: Landing page component loaded");

type Product = {
    product_id: number;
    category_id: number;
    name: string;
    description?: string;
    price: number;
    size?: string;
    color?: string;
    image_url?: string;
    stock_quantity: number;
    is_active: boolean;
};


export default function Products() {

    const [searchParams] = useSearchParams();
    const category = searchParams.get("category") || "all";
    const [products, setProducts] = useState<Product[]>([]);

    useEffect(() => {
        const load = async () => {
            const url =
                category === "all"
                    ? "/api/products"
                    : `/api/products?category=${category}`;

            const res = await fetch(url);
            const data = await res.json();
            setProducts(data);
        };

        load();
    }, [category]);


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
        
        {/* Main Content */}
        <div className="p-10">
            <h2 className="text-2xl font-bold mb-6">Products</h2>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
                {products.map((p) => (
                    <div key={p.product_id} className="border p-4 rounded-lg shadow">
                        <img src={p.image_url} alt={p.name} className="w-full h-48 object-cover rounded" />
                        <h3 className="mt-4 text-lg font-semibold">{p.name}</h3>
                        <p className="text-gray-600">${p.price}</p>
                        <p className="text-sm text-gray-500">Size: {p.size}</p>
                        <p className="text-sm text-gray-500">Color: {p.color}</p>
                    </div>
                ))}
            </div>

        </div>
        
        </>
    );
}