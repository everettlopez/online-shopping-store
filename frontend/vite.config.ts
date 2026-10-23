import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// Store identity used in index.html and src/config/store.ts when the owner hasn't
// set it (see .env.example). Filled in here so the page title never shows a raw
// %VITE_STORE_NAME% placeholder.
const STORE_DEFAULTS: Record<string, string> = {
  VITE_STORE_NAME: "Online Store",
  VITE_STORE_DESCRIPTION: "Shop our latest products.",
};

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  for (const [name, value] of Object.entries(STORE_DEFAULTS)) {
    if (!env[name]?.trim()) process.env[name] = value;
  }

  return {
    plugins: [react()],
    resolve: {
      dedupe: ["react", "react-dom"]
    },
    server: {
      proxy: {
        "/api": {
          target: "http://127.0.0.1:8000",
          changeOrigin: true,
        }
      }
    }
  };
});
