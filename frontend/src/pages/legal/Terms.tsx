import { Link } from "react-router-dom";
import { store } from "../../config/store";
import LegalPage, { ContactLine } from "./LegalPage";

export default function Terms() {
    return (
        <LegalPage title="Terms of Service">
            <p>
                These terms apply when you use {store.name} or buy from it. The store is run
                by {store.businessName}. By placing an order, you agree to them.
            </p>

            <h2>Orders</h2>
            <p>
                When you place an order, we email a confirmation. We may cancel an order and refund it in full if an
                item turns out to be unavailable, if a price was listed in error, or if we suspect fraud.
            </p>

            <h2>Prices and payment</h2>
            <p>
                Prices are in US dollars. Shipping and any sales tax are shown at checkout before you pay. Payments
                are processed securely by Stripe.
            </p>

            <h2>Shipping and returns</h2>
            <p>
                We ship within the United States. Our <Link to="/shipping-returns">Shipping &amp; Returns</Link> page
                explains shipping costs, returns, and refunds.
            </p>

            <h2>Accounts</h2>
            <p>
                You don't need an account to shop. If you create one, keep your password private; you're responsible
                for orders placed from your account.
            </p>

            <h2>Product information</h2>
            <p>
                We describe and photograph our products as accurately as we can, but colors and sizes can vary
                slightly from what you see on screen.
            </p>

            <h2>Limitation of liability</h2>
            <p>
                To the extent the law allows, our liability for any order is limited to the amount you paid for it.
                Nothing in these terms limits rights you have under consumer protection law.
            </p>

            {store.businessState && (
                <>
                    <h2>Governing law</h2>
                    <p>These terms are governed by the laws of the state of {store.businessState}.</p>
                </>
            )}

            <h2>Changes</h2>
            <p>We may update these terms; the version on this page when you order applies to that order.</p>

            <h2>Questions</h2>
            <p>For questions about these terms, <ContactLine />.</p>
        </LegalPage>
    );
}
