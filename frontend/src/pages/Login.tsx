import { useState } from "react";
import { useAuth } from "../context/AuthContext";

function Login() {
    const { login } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");

    const handleLogin = async(e: React.SubmitEvent) => {
        e.preventDefault();

        try {
            await login(email, password)
            setMessage("Login Successful");
        }
        catch (err: any){
            setMessage("Login failed.");
            console.error(err);
        }
    };

    return (
        <div className="login-container">
            <h1>Login Test</h1>

            <form onSubmit={handleLogin}>
                <label>Email: <input type="email" placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)}/> </label>
                <label>Password: <input type="password" placeholder="password" value={password} onChange={(e) => setPassword(e.target.value)}/> </label>
                <button type="submit">Submit</button>
            </form>

            <p>{message}</p>
        </div>
    );
}

export default Login;