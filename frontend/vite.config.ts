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
  },
  test: {
    environment: "jsdom",
  },
});
