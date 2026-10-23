import AppRouter from "./router/AppRouter";
import { AuthProvider } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";
import { CategoriesProvider } from "./context/CategoriesContext";

console.log("DEBUG: App.tsx rendering");

function App() {
  console.log("DEBUG: AuthProvider is wrapping children");
  return (
    <AuthProvider>
      <CartProvider>
        <CategoriesProvider>
          <AppRouter  />
        </CategoriesProvider>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
