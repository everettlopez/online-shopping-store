import { useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api/auth";
import { apiErrorMessage } from "../api/errors";
import { AuthCard, TextField } from "../components/AuthCard";

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
        <AuthCard title="Forgot Password">
            <p className="text-sm text-gray-600">Enter your account's email and we'll send you a link to choose a new password.</p>

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                <TextField label="Email" type="email" autoComplete="email" required value={email} onChange={setEmail} />

                <button disabled={sending} className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full disabled:opacity-50">
                    {sending ? "Sending..." : "Send reset link"}
                </button>
                {message && <p role="status" className="text-center text-sm">{message}</p>}

                <Link to="/login" className="flex justify-center items-center px-5 py-2 rounded-full border hover:bg-gray-100 transition">
                    Back to sign in
                </Link>
            </form>
        </AuthCard>
    );
}

export default ForgotPassword;
