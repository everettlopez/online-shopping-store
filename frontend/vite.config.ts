import { defineConfig, loadEnv, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Store identity used in index.html and src/config/store.ts when the owner hasn't
// set it (see .env.example).
const STORE_DEFAULTS: Record<string, string> = {
  VITE_STORE_NAME: "Online Store",
  VITE_STORE_DESCRIPTION: "Shop our latest products.",
  VITE_FAVICON_URL: "/favicon.svg",
};

// The page's title, description and icon, and the tags that shared links preview with (Open Graph, read by Facebook,
// iMessage, Slack and others, plus Twitter/X). Link previews don't run the app's
// JavaScript, so every page shares the store's name, description and image. A preview
// image needs a full address, so it's added only when VITE_SITE_URL is set. Vite escapes
// attribute values but not the title's text, which is escaped here.
function storeMeta(env: Record<string, string>): Plugin {
  const setting = (name: string) => env[name]?.trim() || process.env[name]?.trim() || "";

  return {
    name: "store-meta",
    transformIndexHtml() {
      const name = setting("VITE_STORE_NAME");
      const description = setting("VITE_STORE_DESCRIPTION");
      const favicon = setting("VITE_FAVICON_URL");
      const siteUrl = setting("VITE_SITE_URL").replace(/\/+$/, "");
      const imagePath = setting("VITE_SHARE_IMAGE_URL") || setting("VITE_HERO_IMAGE_URL");
      const image = imagePath && (/^https?:\/\//.test(imagePath) ? imagePath : siteUrl && `${siteUrl}${imagePath.startsWith("/") ? "" : "/"}${imagePath}`);

      const meta = (attr: "name" | "property", key: string, content: string) =>
        ({ tag: "meta", attrs: { [attr]: key, content }, injectTo: "head" as const });

      const text = name.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

      return [
        { tag: "title", children: text, injectTo: "head" },
        meta("name", "description", description),
        { tag: "link", attrs: { rel: "icon", href: favicon }, injectTo: "head" },
        meta("property", "og:type", "website"),
        meta("property", "og:site_name", name),
        meta("property", "og:title", name),
        meta("property", "og:description", description),
        ...(siteUrl ? [meta("property", "og:url", `${siteUrl}/`)] : []),
        ...(image ? [meta("property", "og:image", image), meta("name", "twitter:image", image)] : []),
        meta("name", "twitter:card", image ? "summary_large_image" : "summary"),
        meta("name", "twitter:title", name),
        meta("name", "twitter:description", description),
      ];
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  for (const [name, value] of Object.entries(STORE_DEFAULTS)) {
    if (!env[name]?.trim()) process.env[name] = value;
  }

  return {
    plugins: [react(), tailwindcss(), storeMeta(env)],
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
