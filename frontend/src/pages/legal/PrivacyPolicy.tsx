import { store } from "../../config/store";
import LegalPage, { ContactLine } from "./LegalPage";

export default function PrivacyPolicy() {
    return (
        <LegalPage title="Privacy Policy">
            <p>
                This policy explains what personal information {store.businessName} collects when you shop
                at {store.name}, how we use it, and the choices you have.
            </p>

            <h2>What we collect</h2>
            <ul>
                <li>Your name, email address, phone number, and shipping and billing addresses, when you place an order or save them to your account.</li>
                <li>Your order history: what you bought, what you paid, and shipping and tracking details.</li>
                <li>Your account details, if you create one: your name, email address, and a securely hashed password (we never store the password itself).</li>
            </ul>

            <h2>Payments</h2>
            <p>
                Payments are processed by Stripe. Your card or other payment details go directly to Stripe and
                never reach our servers; we only see the payment method type and, for cards, the brand and last
                four digits. Stripe also calculates sales tax from your address. See{" "}
                <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer">Stripe's privacy policy</a>.
            </p>

            <h2>How we use your information</h2>
            <ul>
                <li>To process, ship, and support your orders, and to send order confirmations, shipping notices, and password reset emails.</li>
                <li>To keep records of sales as the law requires.</li>
                <li>To protect the store against fraud and abuse.</li>
            </ul>
            <p>We don't sell your personal information, and we don't send marketing email.</p>

            <h2>Who we share it with</h2>
            <ul>
                <li>Stripe, to take payments and calculate tax.</li>
                <li>Our email provider, to deliver the emails above.</li>
                <li>Shipping carriers, who receive your name and shipping address to deliver your order.</li>
                <li>Authorities, when the law requires it.</li>
            </ul>

            <h2>Cookies and browser storage</h2>
            <p>
                When you log in, we set one cookie that keeps you signed in. If you shop without an account, your
                cart is saved in your browser's storage on your device. We don't use advertising or tracking
                cookies.
            </p>

            <h2>How long we keep it</h2>
            <p>
                We keep order records for as long as tax and accounting rules require. You can delete your account
                from your account page; if you've placed orders, we keep those order records but you can ask us to
                remove anything we aren't required to keep.
            </p>

            <h2>Your choices</h2>
            <p>
                You can view and update your account details and addresses at any time. To ask for a copy of your
                information, a correction, or its deletion, <ContactLine />.
            </p>

            <h2>Children</h2>
            <p>This store isn't directed to children under 13, and we don't knowingly collect their information.</p>

            <h2>Changes</h2>
            <p>If we change this policy, we'll update this page.</p>
        </LegalPage>
    );
}
