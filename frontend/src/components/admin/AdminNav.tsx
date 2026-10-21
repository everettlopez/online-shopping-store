import { Link } from "react-router-dom";

export default function AdminNav() {
    return (
        <div className="relative flex flex-col justify-center items-center gap-4 p-5">
            <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

            <nav className="flex gap-12">
                <Link to="/admin/products"><p className="text-base font-normal tracking-widest">PRODUCTS</p></Link>
                <Link to="/admin/categories"><p className="text-base font-normal tracking-widest">CATEGORIES</p></Link>
                <Link to="/admin/users"><p className="text-base font-normal tracking-widest">USERS</p></Link>
                <Link to="/admin/orders"><p className="text-base font-normal tracking-widest">ORDERS</p></Link>
            </nav>
        </div>
    );
}
