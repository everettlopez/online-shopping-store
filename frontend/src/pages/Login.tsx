import { useState } from "react";
import { useAuth } from "../context/useAuth";
import { Link, useLocation } from "react-router-dom";
import { AuthCard, TextField } from "../components/AuthCard";
import { apiErrorMessage } from "../api/errors";


function Login() {
    const { login } = useAuth();
    // Carried to register, so either way the shopper returns where they started
    const { state } = useLocation();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");

    const handleLogin = async(e: React.SubmitEvent) => {
        e.preventDefault();

        try {
            await login(email, password)
            setMessage("Login Successful");
        }
        catch (err){
            // e.g. "Invalid credentials", or the rate limit's "Too many attempts"
            setMessage(apiErrorMessage(err, "Login failed."));
            console.error(err);
        }
    };

    return (
        <AuthCard title="Sign In" backTo="/">
            <form onSubmit={handleLogin} className="flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                    <TextField label="Email" type="email" placeholder="you@example.com" autoComplete="email" required
                        value={email} onChange={setEmail} />
                    <TextField label="Password" type="password" placeholder="password" autoComplete="current-password" required
                        value={password} onChange={setPassword} />
                    <Link to="/forgot-password" className="self-end text-sm underline">Forgot password?</Link>
                </div>

                <button className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full">Login</button>
                {message && <p role="status" className="text-center text-sm">{message}</p>}
                <Link
                    to="/register"
                    state={state}
                    className="flex justify-center items-center px-5 py-2 rounded-full border hover:bg-gray-100 transition"
                >
                    Create new account
                </Link>
            </form>
        </AuthCard>
    );
}

export default Login;