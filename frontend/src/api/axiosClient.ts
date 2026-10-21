import axios from "axios";

// Set VITE_API_URL at build time for production (see frontend/.env.example);
// the fallback is the local dev API
const axiosClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api",
    withCredentials: true,
});

export default axiosClient;
