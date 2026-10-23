import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { lookUpOrder, trackingPath } from "../api/orders";
import { apiErrorMessage } from "../api/errors";
import { useAuth } from "../context/useAuth";
import Navbar from "../components/Navbar";
import { TextField } from "../components/AuthCard";

// Find an order without an account, from its number and the email it was placed with
export default function TrackOrder() {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [orderNumber, setOrderNumber] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");
    const [searching, setSearching] = useState(false);

    const handleSubmit = async (e: React.SubmitEvent) => {
        e.preventDefault();
        setSearching(true);
        setError("");

        try {
            // A leading "#" is how order numbers are shown on the order pages
            const found = await lookUpOrder(orderNumber.trim().replace(/^#/, ""), email.trim());
            navigate(trackingPath(found.order_number, found.access_token));
        }
        catch (err) {
            setError(apiErrorMessage(err, "We couldn't look up that order. Please try again."));
        }
        finally {
            setSearching(false);
        }
    };

    return (
        <>
        <Navbar />
        <main>
        <div className="flex justify-center items-center bg-gray-100 py-16 px-4">
            <div className="flex flex-col justify-center border w-full max-w-[400px] p-6 sm:p-10 gap-6 bg-white rounded-[20px] shadow-sm">
                <h1 className="text-3xl sm:text-4xl">Track your order</h1>
                <p className="text-sm text-gray-600">
                    Enter the order number from your confirmation email and the email you checked out with.
                </p>

                <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                    <TextField label="Order number" required value={orderNumber} onChange={setOrderNumber} />
                    <TextField label="Email" type="email" autoComplete="email" required value={email} onChange={setEmail} />

                    <button disabled={searching} className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full disabled:opacity-50">
                        {searching ? "Looking..." : "Find my order"}
                    </button>
                    {error && <p role="alert" className="text-center text-sm text-red-600">{error}</p>}

                    {isAuthenticated ? (
                        <Link to="/orders" className="text-center text-sm underline">See all your orders</Link>
                    ) : (
                        <p className="text-center text-sm text-gray-500">
                            Ordered with an account? <Link to="/login" state={{ from: "/orders" }} className="underline">Log in</Link> to see all your orders.
                        </p>
                    )}
                </form>
            </div>
        </div>
        </main>
        </>
    );
}
