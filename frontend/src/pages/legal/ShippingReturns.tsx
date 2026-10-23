import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getShippingRates, type ShippingRates } from "../../api/shipping";
import { store } from "../../config/store";
import LegalPage, { ContactLine } from "./LegalPage";

const dollars = (amount: number) => `$${amount.toFixed(2)}`;

export default function ShippingReturns() {
    const [rates, setRates] = useState<ShippingRates | null>(null);

    useEffect(() => {
        getShippingRates()
            .then(setRates)
            .catch((err) => console.error("Failed to load shipping rates:", err));
    }, []);

    return (
        <LegalPage title="Shipping & Returns">
            <h2>Shipping</h2>
            <p>We ship within the United States.</p>
            {rates && (
                <p>
                    {rates.flat_rate > 0
                        ? <>Shipping is a flat {dollars(rates.flat_rate)} per order</>
                        : <>Shipping is free on every order</>}
                    {rates.flat_rate > 0 && (
                        <>, and free on orders of {dollars(rates.free_shipping_threshold)} or more</>
                    )}
                    . Sales tax, where it applies, is calculated at checkout.
                </p>
            )}
            <p>
                You'll get an email with a tracking number when your order ships. You can also check on an order
                any time from <Link to="/track">Track an Order</Link> with your order number and email address.
            </p>

            <h2>Returns</h2>
            <p>
                You can return an item within {store.returnDays} days of delivery if it's unused and in its original
                condition. To start a return, <ContactLine /> with your order number and the item you'd like to return,
                and we'll send you return instructions.
            </p>

            <h2>Refunds</h2>
            <p>
                Once we receive and check your return, we'll refund the item's price to your original payment method.
                Depending on your bank, the refund can take several business days to appear. Original shipping
                charges aren't refunded unless the item arrived damaged or we sent the wrong item.
            </p>

            <h2>Damaged or wrong items</h2>
            <p>
                If something arrives damaged or isn't what you ordered, <ContactLine /> within a few days of delivery
                and we'll make it right.
            </p>
        </LegalPage>
    );
}
