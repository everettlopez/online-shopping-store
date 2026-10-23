import { Link } from "react-router-dom";
import { store } from "../../config/store";
import LegalPage from "./LegalPage";

export default function Contact() {
    return (
        <LegalPage title="Contact">
            {store.supportEmail ? (
                <p>
                    Questions about an order, a return, or anything else? Email us at{" "}
                    <a href={`mailto:${store.supportEmail}`}>{store.supportEmail}</a> and include your order number
                    if you have one. You can also reply to any email we've sent you.
                </p>
            ) : (
                <p>
                    Questions about an order, a return, or anything else? Reply to your order confirmation email
                    and include your order number.
                </p>
            )}

            <p>
                To check on an order, use <Link to="/track">Track an Order</Link> with your order number and the
                email address you used at checkout.
            </p>

            {store.businessAddress && (
                <>
                    <h2>Mailing address</h2>
                    <p>{store.businessName}<br />{store.businessAddress}</p>
                </>
            )}
        </LegalPage>
    );
}
