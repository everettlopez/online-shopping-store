import { Link, useLocation } from "react-router-dom";
import { store } from "../config/store";

// A policy link: the owner's own page when they set one, else the built-in page
function PolicyLink({ to, url, children }: { to: string; url: string; children: React.ReactNode }) {
    const className = "hover:text-black transition";
    return url
        ? <a href={url} className={className} target="_blank" rel="noopener noreferrer">{children}</a>
        : <Link to={to} className={className}>{children}</Link>;
}

export default function Footer() {
    const { pathname } = useLocation();

    // The admin pages are a tool, not part of the storefront
    if (pathname.startsWith("/admin")) return null;

    return (
        <footer className="border-t mt-16 px-5 py-8 flex flex-col items-center gap-4 text-sm text-gray-600">
            <nav className="flex flex-wrap justify-center gap-x-8 gap-y-2" aria-label="Store policies">
                <PolicyLink to="/shipping-returns" url={store.policyUrls.shipping}>Shipping &amp; Returns</PolicyLink>
                <PolicyLink to="/privacy" url={store.policyUrls.privacy}>Privacy Policy</PolicyLink>
                <PolicyLink to="/terms" url={store.policyUrls.terms}>Terms of Service</PolicyLink>
                <Link to="/contact" className="hover:text-black transition">Contact</Link>
                <Link to="/track" className="hover:text-black transition">Track an Order</Link>
            </nav>
            <p>&copy; {new Date().getFullYear()} {store.businessName}</p>
        </footer>
    );
}
