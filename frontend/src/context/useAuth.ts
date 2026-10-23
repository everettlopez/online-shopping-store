// The auth context and its hook, kept apart from AuthProvider so that file exports
// only a component (which React Fast Refresh needs)
import { createContext, useContext } from "react";

export interface User {
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

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if(!ctx) throw new Error("useAuth must be inside AuthProvider");
    return ctx;
};
