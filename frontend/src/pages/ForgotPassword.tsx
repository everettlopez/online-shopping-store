import { useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api/auth";
import { apiErrorMessage } from "../api/errors";

function ForgotPassword() {
    const [email, setEmail] = useState("");
    const [message, setMessage] = useState("");
    const [sending, setSending] = useState(false);

    const handleSubmit = async (e: React.SubmitEvent) => {
        e.preventDefault();
        setSending(true);

        try {
            const data = await forgotPassword(email);
            setMessage(data.message);
        }
        catch (err) {
            setMessage(apiErrorMessage(err, "We couldn't send the email. Please try again."));
        }
        finally {
            setSending(false);
        }
    };

    return (
        <div className="min-h-screen flex justify-center items-center bg-gray-100">
            <div className="flex flex-col justify-center border w-[400px] p-10 gap-6 bg-white rounded-[20px] shadow-sm">
                <h1 className="text-4xl">Forgot Password</h1>
                <p className="text-sm text-gray-600">Enter your account's email and we'll send you a link to choose a new password.</p>

                <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                    <div className="flex flex-col border p-2 rounded-[10px] gap-1">
                        <label className="text-sm" htmlFor="forgot-email">Email</label>
                        <input id="forgot-email" type="email" required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="h-[32px] text-[24px] border-none focus:outline-hidden focus:ring-0" />
                    </div>

                    <button disabled={sending} className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full disabled:opacity-50">
                        {sending ? "Sending..." : "Send reset link"}
                    </button>
                    {message && <p className="text-center text-sm">{message}</p>}

                    <Link to="/login" className="flex justify-center items-center px-5 py-2 rounded-full border hover:bg-gray-100 transition">
                        Back to sign in
                    </Link>
                </form>
            </div>
        </div>
    );
}

export default ForgotPassword;
