import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During dev, proxy /api to the backend so the frontend can call it without CORS
// hassle. In production the frontend uses VITE_API_BASE (the Cloud Run URL).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8080",
    },
    // Permit Cloudflare Tunnel hostnames so the dev server can be exposed
    // publicly for a demo. Vite otherwise rejects unrecognised Host headers
    // as DNS-rebinding protection. Dev server only; the production build is
    // unaffected and still targets VITE_API_BASE.
    allowedHosts: [".trycloudflare.com"],
  },
  test: {
    environment: "jsdom",
  },
});
