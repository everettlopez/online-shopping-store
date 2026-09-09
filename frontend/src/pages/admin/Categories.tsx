import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function AdminCategories() {

    type Category = {
        category_id: number;
        name: string;
        description: string;
    };

    const [categories, setCategories] = useState<Category[]>([]);

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const res = await fetch("http://127.0.0.1:8000/api/categories", {
                    credentials: "include",
                });

                if(!res.ok) {
                    console.error("Failed to fetch categories");
                    return;
                }

                const data = await res.json();
                console.log("ADMIN CATEGORY RESPONSE: ", data)
                setCategories(data.categories);

            }
            catch (err) {
                console.error("Error fetching categories:", err)
            }
        };

        fetchCategories();

    }, []);



    return (
        <>

        {/* Header */}
        <div className="relative flex flex-col justify-center items-center gap-4 p-5">
            <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

            <nav className="flex gap-12">
            <Link to="/admin/products">
                <p className="text-base font-normal tracking-widest">PRODUCTS</p>
            </Link>
            <Link to="/admin/categories">
                <p className="text-base font-normal tracking-widest">CATEGORIES</p>
            </Link>
            <Link to="/admin/users">
                <p className="text-base font-normal tracking-widest">USERS</p>
            </Link>
            <Link to="/admin/orders">
                <p className="text-base font-normal tracking-widest">ORDERS</p>
            </Link>
            </nav>
        </div>

        <div className="p-6 border rounded-lg bg-white shadow-sm flex flex-col gap-4">

            {/* Header */}
            <div className="grid grid-cols-4 gap-4 text-sm font-semibold text-gray-500 border-b pb-2">
                <div className="text-center tracking-wider">CATEGORY ID</div>
                <div className="text-center tracking-wider">NAME</div>
                <div className="text-center tracking-wider">DESCRIPTION</div>
                <div className="text-center tracking-wider">ACTIONS</div>
            </div>

            {categories.map(category => (
                <div key={category.category_id} className="grid grid-cols-4 gap-4 py-2">
                    <div className="text-center">{category.category_id}</div>
                    <div className="text-center">{category.name}</div>
                    <div className="text-center">{category.description}</div>

                    {/* Actions Buttons */}
                    <div className="flex justify-center gap-2">
                        <button className="border rounded-[10px] px-8 py-1 hover:bg-gray-300">Update</button>
                        <button className="border rounded-[10px] px-8 py-1 bg-red-500 text-white hover:bg-red-600">Delete</button>
                    </div>
                </div>
            ))}

        </div>
        </>
    );
}

