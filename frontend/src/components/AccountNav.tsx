import { NavLink } from "react-router-dom";
import { useAuth } from "../context/useAuth";

// The account pages' menu: a row of links (wrapping if needed) on phones, a column beside
// the page from 768 px
export default function AccountNav() {
    const { user } = useAuth();

    const links = [
        { to: "/account", label: "ACCOUNT", end: true },
        { to: "/orders", label: "ORDERS", end: false },
        { to: "/track", label: "TRACK AN ORDER", end: false },
        ...(user?.is_admin ? [{ to: "/admin", label: "ADMIN", end: false }] : []),
    ];

    return (
        <nav aria-label="Account" className="md:w-48 md:shrink-0">
            <ul className="flex flex-wrap md:flex-col gap-x-5 gap-y-3 md:items-end md:pt-2">
                {links.map((link) => (
                    <li key={link.to}>
                        <NavLink
                            to={link.to}
                            end={link.end}
                            className={({ isActive }) =>
                                `text-sm md:text-base tracking-widest hover:text-gray-600 ${isActive ? "underline underline-offset-8" : ""}`}
                        >
                            {link.label}
                        </NavLink>
                    </li>
                ))}
            </ul>
        </nav>
    );
}
