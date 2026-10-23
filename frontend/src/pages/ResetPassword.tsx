import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { resetPassword } from "../api/auth";
import { apiErrorMessage } from "../api/errors";
import { AuthCard, TextField } from "../components/AuthCard";

function ResetPassword() {
    const [searchParams] = useSearchParams();
    const token = searchParams.get("token") ?? "";

    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [message, setMessage] = useState("");
    const [done, setDone] = useState(false);
    const [saving, setSaving] = useState(false);

    const handleSubmit = async (e: React.SubmitEvent) => {
        e.preventDefault();

        if (password !== confirm) {
            setMessage("The passwords don't match");
            return;
        }

        setSaving(true);
        try {
            const data = await resetPassword(token, password);
            setMessage(data.message);
            setDone(true);
        }
        catch (err) {
            setMessage(apiErrorMessage(err, "We couldn't reset your password. Please try again."));
        }
        finally {
            setSaving(false);
        }
    };

    return (
        <AuthCard title="Reset Password">

                {!token ? (
                    <p className="text-sm">
                        This link is missing its reset code. Use the link from your email,
                        or <Link to="/forgot-password" className="underline">request a new one</Link>.
                    </p>
                ) : done ? (
                    <>
                        <p className="text-center text-sm">{message}</p>
                        <Link to="/login" className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full">Sign in</Link>
                    </>
                ) : (
                    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                        <div className="flex flex-col gap-2">
                            <TextField label="New password" type="password" autoComplete="new-password" required minLength={8} maxLength={72}
                                value={password} onChange={setPassword} />
                            <TextField label="Confirm new password" type="password" autoComplete="new-password" required
                                value={confirm} onChange={setConfirm} />
                        </div>

                        <button disabled={saving} className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full disabled:opacity-50">
                            {saving ? "Saving..." : "Set new password"}
                        </button>
                        {message && <p role="status" className="text-center text-sm">{message}</p>}

                        <Link to="/forgot-password" className="text-center text-sm underline">Request a new link</Link>
                    </form>
                )}
        </AuthCard>
    );
}

export default ResetPassword;
