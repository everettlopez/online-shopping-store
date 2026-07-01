import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import Login from "../pages/Login";
import Register from "../pages/Register";
import Landing from "../pages/Landing";
import ProductsPage from "../pages/Products";
import Admin from "../pages/admin/Admin";
import AccountPage from "../pages/Account";
import AdminProducts from "../pages/admin/Products";
import AdminUsers from "../pages/admin/Users";
import AdminCategories from "../pages/admin/Categories";
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

function AdminRoute({ children }: { children: React.ReactNode }) {
    const { user, isAuthenticated, loading } = useAuth();

    if (loading) return <p>Loading...</p>;
    if (!isAuthenticated) return <Navigate to="/login" />;

    // user.is_admin must come from your JWT payload
    if (!user?.is_admin) return <Navigate to="/" replace />;

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

            <Route
                path="/admin"
                element={
                    <AdminRoute>
                        <Admin />
                    </AdminRoute>
                }
            />

            <Route 
            path="/admin/products"
            element={
                <AdminRoute>
                    <AdminProducts />
                </AdminRoute>
            }/>

            <Route 
                path="/admin/users"
                element={
                    <ProtectedRoute>
                        <AdminUsers />
                    </ProtectedRoute>
                }/>

            <Route 
                path="/admin/categories"
                element= {
                    <ProtectedRoute>
                        <AdminCategories />
                    </ProtectedRoute>
                }/>
            

            <Route
                path="/account"
                element={
                    <ProtectedRoute>
                        <AccountPage />
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