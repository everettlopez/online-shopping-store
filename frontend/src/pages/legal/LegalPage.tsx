import { useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import { store } from "../../config/store";

// Layout for the policy and contact pages. Their wording is a general starting point
// filled in from src/config/store.ts, not legal advice: each store owner should have
// it reviewed, or link to their own policies with the VITE_*_URL settings.
export default function LegalPage({ title, children }: { title: string; children: React.ReactNode }) {
    useEffect(() => {
        document.title = `${title} | ${store.name}`;
        return () => { document.title = store.name; };
    }, [title]);

    return (
        <>
        <Navbar />
        <main className="max-w-3xl mx-auto px-5 py-10 flex flex-col gap-6 leading-relaxed [&_h2]:text-2xl [&_h2]:mt-4 [&_ul]:list-disc [&_ul]:pl-6 [&_a]:underline">
            <h1 className="text-4xl">{title}</h1>
            {children}
        </main>
        </>
    );
}

// "email support@example.com", or "contact us" when the owner hasn't set an address
export function ContactLine() {
    return store.supportEmail
        ? <>email <a href={`mailto:${store.supportEmail}`}>{store.supportEmail}</a></>
        : <>use the details on our <Link to="/contact">contact page</Link></>;
}
