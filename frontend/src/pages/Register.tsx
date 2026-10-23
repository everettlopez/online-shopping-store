import { useState } from "react";
import axiosClient from "../api/axiosClient";
import { apiErrorMessage } from "../api/errors";
import { useNavigate, useLocation, Link } from  "react-router-dom";
import { AuthCard, TextField } from "../components/AuthCard";


function Register() {
    const navigate = useNavigate();
    // Passed on to login, so the shopper ends up back where they started (e.g. the cart)
    const { state } = useLocation();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [firstName, setFirstName] = useState("");
    const [lastName, setLastName] = useState("");
    const [message, setMessage] = useState("");

    const handleRegister = async(e: React.SubmitEvent) => {
        e.preventDefault();

        try {
            await axiosClient.post("/auth/register", {
                email, 
                password,
                first_name: firstName,
                last_name: lastName,
            });

            setMessage("Registration successful. Redirecting to login...");
            setTimeout(() => navigate("/login", { state }), 800);
        } catch (err) {
            console.error(err);
            setMessage(apiErrorMessage(err, "Registration failed."));
        }
    };

    return (
        <AuthCard title="Create New Account" backTo="/">
            <form onSubmit={handleRegister} className="flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                    <TextField label="First Name" placeholder="Jane" autoComplete="given-name" required
                        value={firstName} onChange={setFirstName} />
                    <TextField label="Last Name" placeholder="Doe" autoComplete="family-name" required
                        value={lastName} onChange={setLastName} />
                    <TextField label="Email" type="email" placeholder="you@example.com" autoComplete="email" required
                        value={email} onChange={setEmail} />
                    <TextField label="Password" type="password" placeholder="at least 8 characters" autoComplete="new-password"
                        minLength={8} required value={password} onChange={setPassword} />
                </div>

                <button type="submit" className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full">Register</button>
                {message && <p role="status" className="text-center text-sm">{message}</p>}
                <Link to="/login" state={state} className="flex justify-center items-center underline">Already have an account? Sign in</Link>
            </form>
        </AuthCard>
    );

}

export default Register;