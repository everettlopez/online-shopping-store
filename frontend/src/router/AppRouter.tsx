import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import Login from "../pages/Login";
import Register from "../pages/Register";
import Landing from "../pages/Landing";
import ProductsPage from "../pages/Products";
// import CartPage from "../pages/Cart";

// TODO: Add routes as needed

function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, loading } = useAuth();

    if (loading) return <p>Loading...</p>;
    if(!isAuthenticated) return <Navigate to="/login"/>;

    return children;
}

function PublicOnlyRoute({children}: {children: React.ReactNode }) {
    const { isAuthenticated, loading } = useAuth();

    if (loading) return <p>Loading...</p>;
    if (isAuthenticated) return <Navigate to="/products" replace />;

    return children;
}

console.log("DEBUG: AppRouter rendering");


export default function AppRouter() {
    console.log("DEBUG: AppRouter loaded");
    return (
        <BrowserRouter>
        <Routes>
            {/* Public Routes */}

            <Route 
                path="/" 
                element={<Landing />}
            />

            <Route 
                path="/login" 
                element={
                    <PublicOnlyRoute>
                        <Login />
                    </PublicOnlyRoute>
                }
            />

            <Route 
                path="/register" 
                element={
                    <PublicOnlyRoute>
                        <Register />
                    </PublicOnlyRoute>
                }
            />

            {/* Protected Routes */}
            <Route 
                path="/products"
                element = {
                    <ProtectedRoute>
                        <ProductsPage />
                    </ProtectedRoute> 
                }
            />

            {/* TODO: Add Accounts Route for Account Page */}
            {/* <Route 
                path="/cart"
                element = {
                    <ProtectedRoute>
                        <CartPage />
                    </ProtectedRoute>
                }/> */}

        </Routes>
        </BrowserRouter>
    );
}