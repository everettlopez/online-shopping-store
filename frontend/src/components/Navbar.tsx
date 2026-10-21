import { Link, useLocation, useSearchParams } from "react-router-dom";
import { useCategories } from "../context/CategoriesContext";

// "New Arrivals" is a fixed link to the newest products, so hide any leftover
// category with that name to avoid showing it twice
const NEW_ARRIVALS = "new arrivals";

interface NavbarProps {
    className?: string;
}

export default function Navbar({ className = "" }: NavbarProps) {
    const { categories } = useCategories();
    const { pathname } = useLocation();
    const [searchParams] = useSearchParams();

    const onProducts = pathname === "/products";
    const activeCategory = onProducts ? searchParams.get("category") : null;
    const newArrivalsActive = onProducts && searchParams.get("sort") === "newest";

    const linkClass = (active: boolean) =>
        `text-base font-normal tracking-widest ${active ? "underline underline-offset-8" : ""}`;

    return (
        <header className={`relative flex flex-col justify-center items-center gap-4 p-5 ${className}`}>

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
            <Link to="/"><h1 className="text-6xl">KILLJOY</h1></Link>

            {/* Navigation */}
            <nav className="flex flex-wrap justify-center gap-x-12 gap-y-2">
                <Link to="/"><p className={linkClass(pathname === "/")}>EVENTS</p></Link>
                <Link to="/products?sort=newest"><p className={linkClass(newArrivalsActive)}>NEW ARRIVALS</p></Link>
                {categories
                    .filter((category) => category.name.trim().toLowerCase() !== NEW_ARRIVALS)
                    .map((category) => (
                        <Link key={category.category_id} to={`/products?category=${category.category_id}`}>
                            <p className={linkClass(activeCategory === String(category.category_id))}>
                                {category.name.toUpperCase()}
                            </p>
                        </Link>
                    ))}
            </nav>
        </header>
    );
}
