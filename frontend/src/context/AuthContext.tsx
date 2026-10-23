import { useEffect, useState } from "react";
import { login as apiLogin, logout as apiLogout, getCurrentUser } from "../api/auth";
import { AuthContext, type User } from "./useAuth";


export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const tryRestoreSession = async () => {
            try {
                const data = await getCurrentUser();
                setUser(data);
            }
            catch {
                setUser(null);
            } finally {
                setLoading(false);
            }
        };

        tryRestoreSession();
    }, []);


    const login = async (email: string, password: string) => {
        await apiLogin({email, password});

        await new Promise((res) => setTimeout(res, 50));
        
        const data = await getCurrentUser();
        // The login worked but the browser didn't keep its cookie (blocked cross-site cookies)
        if (!data) throw new Error("Your browser blocked the sign-in cookie. Allow cookies for this site and try again.");
        setUser(data);
    };

    const logout = async () => {
        await apiLogout();
        setUser(null);
        // Shopping doesn't need an account, so go back to the store
        window.location.href = "/";
    };


    const refreshUser = async () => {
        try {
            const data = await getCurrentUser();
            setUser(data);
        } catch {
            setUser(null);
        }
    };


    return (
        <AuthContext.Provider 
            value = {{
                user, 
                loading, 
                isAuthenticated: !!user,
                login,
                logout,
                refreshUser,
            }}>
                {children}
            </AuthContext.Provider>
    );
};
