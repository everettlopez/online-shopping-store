import { useState } from "react";
import { useAuth } from "../context/AuthContext";

console.log("DEBUG: Login component loaded");


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
        <>
        {/* Login Frame */}
        <div className="min-h-screen flex justify-center items-center bg-gray-100">

            <div className="flex flex-col justify-center border w-[400px] p-10 gap-6 bg-white rounded-[20px] shadow">
                <h1 className="text-4xl">Sign In</h1>

                <form onSubmit={handleLogin}>

                    <div className="flex flex-col gap-5">

                        <div className="flex flex-col gap-2">
                            <div className="flex flex-col border p-2 rounded-[10px] gap-1">
                                <label className="text-sm">Email</label>
                                <input type="text" placeholder="everett@gmail.com"
                                    value={email}
                                    onChange = {(e) => setEmail(e.target.value)}
                                    className="h-[32px] text-[24px] border-none focus:outline-none focus:ring-0" />
                            </div>

                            <div className="flex flex-col border p-2 rounded-[10px] gap-1">
                                <label className="text-sm">Password</label>
                                <input type="password" placeholder="password"
                                    value={password}
                                    onChange = {(e) => setPassword(e.target.value)}
                                    className="h-[32px] text-[24px] border-none focus:outline-none focus:ring-0" />
                            </div>
                        </div>

                        <button className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full">Login</button>
                    </div>
                </form>
            </div>
        </div>
        </>
    );
}

export default Login;