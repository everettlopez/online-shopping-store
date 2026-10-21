import AppRouter from "./router/AppRouter";
import { AuthProvider } from "./context/AuthContext";
import { CategoriesProvider } from "./context/CategoriesContext";

console.log("DEBUG: App.tsx rendering");

function App() {
  console.log("DEBUG: AuthProvider is wrapping children");
  return (
    <AuthProvider>
      <CategoriesProvider>
        <AppRouter  />
      </CategoriesProvider>
    </AuthProvider>
  );
}

export default App;
