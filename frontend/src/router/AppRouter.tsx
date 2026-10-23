import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/useAuth";

import Login from "../pages/Login";
import Register from "../pages/Register";
import ForgotPassword from "../pages/ForgotPassword";
import ResetPassword from "../pages/ResetPassword";
import Landing from "../pages/Landing";
import ProductsPage from "../pages/Products";
import Admin from "../pages/admin/Admin";
import AccountPage from "../pages/Account";
import AdminProducts from "../pages/admin/Products";
import AdminUsers from "../pages/admin/Users";
import AdminCategories from "../pages/admin/Categories";
import CartPage from "../pages/Cart";
import CheckoutPage from "../pages/Checkout";
import OrderSuccessPage from "../pages/OrderSuccess";
import OrdersPage from "../pages/orders/Orders";
import OrderDetailPage from "../pages/orders/OrderDetail";
import AdminOrdersPage from "../pages/admin/Orders";
import TrackOrderPage from "../pages/TrackOrder";
import TrackedOrderPage from "../pages/TrackedOrder";
import PrivacyPolicy from "../pages/legal/PrivacyPolicy";
import Terms from "../pages/legal/Terms";
import ShippingReturns from "../pages/legal/ShippingReturns";
import Contact from "../pages/legal/Contact";
import Footer from "../components/Footer";

// TODO: Add routes as needed

// Account pages only. Shopping, checkout and order tracking work without an account
function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, loading } = useAuth();
    const location = useLocation();

    if (loading) return <p>Loading...</p>;
    // Come back here after logging in
    if(!isAuthenticated) return <Navigate to="/login" state={{ from: location.pathname + location.search }}/>;

    return children;
}

// Where to go after logging in: the page that sent the shopper to log in, if it's one of ours
function returnPath(state: unknown): string {
    const from = (state as { from?: unknown } | null)?.from;
    // Browsers read "/\evil.com" like "//evil.com" (another site), so refuse backslashes too
    return typeof from === "string" && from.startsWith("/") && !from.startsWith("//") && !from.includes("\\") ? from : "/products";
}

function PublicOnlyRoute({children}: {children: React.ReactNode }) {
    const { isAuthenticated, loading } = useAuth();
    const location = useLocation();

    if (loading) return <p>Loading...</p>;
    if (isAuthenticated) return <Navigate to={returnPath(location.state)} replace />;

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



export default function AppRouter() {
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

            <Route
                path="/forgot-password"
                element={
                    <PublicOnlyRoute>
                        <ForgotPassword />
                    </PublicOnlyRoute>
                }
            />

            <Route
                path="/reset-password"
                element={
                    <PublicOnlyRoute>
                        <ResetPassword />
                    </PublicOnlyRoute>
                }
            />

            {/* Shopping and order tracking: open to everyone */}
            <Route path="/track" element={<TrackOrderPage />} />
            <Route path="/track/:order_number" element={<TrackedOrderPage />} />

            {/* Store policies and contact details, filled in from src/config/store.ts */}
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/shipping-returns" element={<ShippingReturns />} />
            <Route path="/contact" element={<Contact />} />

            {/* Products, cart, checkout and the success page are open to guests; account and admin pages need a login */}
            <Route 
                path="/products"
                element = {
                    <ProductsPage />
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
                path="/admin/orders"
                element={
                    <AdminRoute>
                        <AdminOrdersPage />
                    </AdminRoute>
                }/>

            <Route 
                path="/admin/users"
                element={
                    <AdminRoute>
                        <AdminUsers />
                    </AdminRoute>
                }/>

            <Route 
                path="/admin/categories"
                element= {
                    <AdminRoute>
                        <AdminCategories />
                    </AdminRoute>
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
            <Route 
                path="/cart"
                element = {
                    <CartPage />
                }/>

            <Route 
                path="/checkout"
                element= {
                    <CheckoutPage />
                }/>

            <Route 
                path="/order-success"
                element={
                    <OrderSuccessPage />
                }/>

            <Route 
                path="/orders"
                element={
                    <ProtectedRoute>
                        <OrdersPage />
                    </ProtectedRoute>
                }/>

            <Route 
                path="/orders/:order_number"
                element={
                    <ProtectedRoute>
                        <OrderDetailPage />
                    </ProtectedRoute>
                }/>

        </Routes>
        <Footer />
        </BrowserRouter>
    );
}