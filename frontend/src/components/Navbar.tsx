import { useCallback, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { useCategories } from "../context/useCategories";
import { useAuth } from "../context/useAuth";
import { useCart } from "../context/useCart";
import { store } from "../config/store";
import Drawer from "./Drawer";

// "New Arrivals" is a fixed link to the newest products, so hide any leftover
// category with that name to avoid showing it twice
const NEW_ARRIVALS = "new arrivals";

interface NavbarProps {
    className?: string;
}

export default function Navbar({ className = "" }: NavbarProps) {
    const { categories } = useCategories();
    const { isAuthenticated } = useAuth();
    const { count } = useCart();
    const { pathname } = useLocation();
    const [searchParams] = useSearchParams();
    const [menuOpen, setMenuOpen] = useState(false);
    const closeMenu = useCallback(() => setMenuOpen(false), []);

    const onProducts = pathname === "/products";
    const activeCategory = onProducts ? searchParams.get("category") : null;
    const newArrivalsActive = onProducts && searchParams.get("sort") === "newest";
    const trackActive = pathname.startsWith("/track");

    const linkClass = (active: boolean) =>
        `text-base font-normal tracking-widest ${active ? "underline underline-offset-8" : ""}`;

    // The same links in the row under the logo (768 px and up) and in the menu (below)
    const navLinks = [
        { key: "home", to: "/", label: "HOME", active: pathname === "/" },
        ...(store.eventsUrl ? [{ key: "events", href: store.eventsUrl, label: "EVENTS", active: false }] : []),
        { key: "new", to: "/products?sort=newest", label: "NEW ARRIVALS", active: newArrivalsActive },
        ...categories
            .filter((category) => category.name.trim().toLowerCase() !== NEW_ARRIVALS)
            .map((category) => ({
                key: `category-${category.category_id}`,
                to: `/products?category=${category.category_id}`,
                label: category.name.toUpperCase(),
                active: activeCategory === String(category.category_id),
            })),
    ];

    const renderLink = (link: (typeof navLinks)[number], onClick?: () => void) =>
        "href" in link ? (
            <a key={link.key} href={link.href} onClick={onClick} className={linkClass(link.active)}>{link.label}</a>
        ) : (
            <Link key={link.key} to={link.to} onClick={onClick} className={linkClass(link.active)}>{link.label}</Link>
        );

    const iconClass = "hover:text-gray-600 transition";

    return (
        <header className={`flex flex-col gap-4 px-4 py-4 md:p-5 ${className}`}>

            {/* Menu button, logo and icons. On phones the logo gets whatever the button and icons
                leave (and wraps if it must); from 768 px the side columns match so it's centered. */}
            <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3">
                <div>
                    <button
                        onClick={() => setMenuOpen(true)}
                        aria-label="Menu"
                        aria-expanded={menuOpen}
                        className={`md:hidden text-2xl px-1 ${iconClass}`}
                    >
                        <i className="fa-solid fa-bars" aria-hidden="true"></i>
                    </button>
                </div>

                <Link to="/" className="text-center">
                    <h1 className="text-2xl min-[360px]:text-3xl sm:text-4xl md:text-6xl break-words">{store.logoText}</h1>
                </Link>

                <div className="flex items-center justify-end gap-3 min-[360px]:gap-4 md:gap-6 text-xl md:text-2xl">
                    {/* Order tracking works without an account; a word on wide screens, an icon below.
                        Font Awesome's display rule outranks Tailwind's layered classes, so the
                        icon is hidden through a wrapper. */}
                    <Link to="/track" aria-label="Track order" className={iconClass}>
                        <span className={`hidden lg:inline ${linkClass(trackActive)}`}>TRACK ORDER</span>
                        <span className="lg:hidden"><i className="fa-solid fa-truck-fast" aria-hidden="true"></i></span>
                    </Link>

                    <Link to={isAuthenticated ? "/account" : "/login"} aria-label={isAuthenticated ? "Account" : "Log in"} className={iconClass}>
                        <i className="fa-regular fa-user" aria-hidden="true"></i>
                    </Link>

                    <Link to="/cart" aria-label={`Cart, ${count} items`} className={`relative ${iconClass}`}>
                        <i className="fa-solid fa-bag-shopping" aria-hidden="true"></i>
                        {count > 0 && (
                            <span className="absolute -top-2 -right-3 min-w-5 h-5 px-1 rounded-full bg-black text-white text-xs flex items-center justify-center">
                                {count > 99 ? "99+" : count}
                            </span>
                        )}
                    </Link>
                </div>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex flex-wrap justify-center gap-x-12 gap-y-2">
                {navLinks.map((link) => renderLink(link))}
            </nav>

            <Drawer open={menuOpen} onClose={closeMenu} title="MENU">
                <nav className="flex flex-col gap-5">
                    {navLinks.map((link) => renderLink(link, closeMenu))}
                    <hr />
                    <Link to="/track" onClick={closeMenu} className={linkClass(trackActive)}>TRACK ORDER</Link>
                    <Link to={isAuthenticated ? "/account" : "/login"} onClick={closeMenu} className={linkClass(false)}>
                        {isAuthenticated ? "ACCOUNT" : "LOG IN"}
                    </Link>
                </nav>
            </Drawer>
        </header>
    );
}
