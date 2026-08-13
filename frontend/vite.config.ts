import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 4100,
    cors: true,
    proxy: {
      "/api/langgraph": {
        target: "http://127.0.0.1:2024",
        changeOrigin: true,
        rewrite: (p) => p.replace(new RegExp("^/api/langgraph"), ""),
      },
    },
  },
});
