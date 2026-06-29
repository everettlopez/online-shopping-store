import { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, logout as apiLogout, getCurrentUser } from "../api/auth";

interface User {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    is_admin: boolean;
    created_at: string;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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
        setUser(data);
    };

    const logout = async () => {
        await apiLogout();
        setUser(null);
        window.location.href = "/login";
    };


    const refreshUser = async () => {
        try {
            const data = await getCurrentUser();
            setUser(data);
        } catch {
            setUser(null);
        }
    };


    console.log("DEBUG: AuthProvider mounted");

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

// Hook
export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if(!ctx) throw new Error("useAuth must be inside AuthProvider");
    return ctx;
};