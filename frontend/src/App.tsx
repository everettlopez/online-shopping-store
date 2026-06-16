import AppRouter from "./router/AppRouter";
import { AuthProvider } from "./context/AuthContext";

console.log("DEBUG: App.tsx rendering");

function App() {
  console.log("DEBUG: AuthProvider is wrapping children");
  return (
    <AuthProvider>
      
      <AppRouter  />
    </AuthProvider>
  );
}

export default App;
