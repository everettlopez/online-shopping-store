import { NavLink } from "react-router-dom";
import { store } from "../../config/store";

const LINKS = [
    { to: "/admin/products", label: "PRODUCTS" },
    { to: "/admin/categories", label: "CATEGORIES" },
    { to: "/admin/users", label: "USERS" },
    { to: "/admin/orders", label: "ORDERS" },
];

export default function AdminNav() {
    return (
        <div className="flex flex-col justify-center items-center gap-3 md:gap-4 px-4 py-4 md:p-5">
            <a href="/" className="text-center"><h1 className="text-3xl sm:text-4xl md:text-6xl break-words">{store.logoText}</h1></a>

            {/* Four short links: they wrap onto a second row on narrow screens */}
            <nav className="flex flex-wrap justify-center gap-x-6 gap-y-2 md:gap-x-12">
                {LINKS.map((link) => (
                    <NavLink
                        key={link.to}
                        to={link.to}
                        className={({ isActive }) =>
                            `text-sm md:text-base font-normal tracking-widest ${isActive ? "underline underline-offset-8" : ""}`}
                    >
                        {link.label}
                    </NavLink>
                ))}
            </nav>
        </div>
    );
}
