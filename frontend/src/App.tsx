import AppRouter from "./router/AppRouter";
import { AuthProvider } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";
import { CategoriesProvider } from "./context/CategoriesContext";

function App() {
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
