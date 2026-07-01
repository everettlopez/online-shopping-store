import { useState } from "react";
import axiosClient from "../api/axiosClient";
import { useNavigate, Link } from  "react-router-dom";

console.log("DEBUG: Register component loaded");


function Register() {
    const navigate = useNavigate();

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
            setTimeout(() => navigate("/login"), 800);
        } catch (err: any) {
            console.error(err);
            setMessage("Registration failed.");
        }
    };

    return (
        <>
        {/* Register Frame */}
        <div className="min-h-screen flex justify-center items-center bg-gray-100">

            <div className="flex flex-col justify-center border w-[400px] p-10 gap-6 bg-white rounded-[20px] shadow">
                <h1 className="text-4xl">Create New Account</h1>

                <form onSubmit={handleRegister}>

                    <div className="flex flex-col gap-5">

                        <div className="flex flex-col gap-2">
                            <div className="flex flex-col border p-2 rounded-[10px] gap-1">
                                <label className="text-sm">First Name</label>
                                <input type="text" placeholder="Everett"
                                    value={firstName}
                                    onChange = {(e) => setFirstName(e.target.value)}
                                    className="h-[32px] text-[24px] border-none focus:outline-none focus:ring-0"/>
                            </div>

                            <div className="flex flex-col border p-2 rounded-[10px] gap-1">
                                <label className="text-sm">Last Name</label>
                                <input type="text" placeholder="Lopez"
                                    value={lastName}
                                    onChange = {(e) => setLastName(e.target.value)}
                                    className="h-[32px] text-[24px] border-none focus:outline-none focus:ring-0" />
                            </div>

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

                        <button type="submit" className="flex justify-center items-center bg-black text-white px-5 py-2 rounded-full">Register</button>
                        <Link to="/login" className="flex justify-center items-center ">Already Have An Account? Sign In</Link>
                    </div>
                </form>
            </div>
        </div>
        </>
    );

}

export default Register;