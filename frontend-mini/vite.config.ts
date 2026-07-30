import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({ base: "/labs/trip-weather/", plugins: [react()], server: { proxy: { "/api": "http://localhost:8080" } }, test: { environment: "jsdom" } });
