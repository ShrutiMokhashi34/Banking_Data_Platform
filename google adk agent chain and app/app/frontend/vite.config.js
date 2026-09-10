import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],

  server: {
    host: "0.0.0.0",
    port: 5173,

    proxy: {
      "/auth": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },

      "/api/chat": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
        rewrite: (path) =>
          path.replace(/^\/api\/chat/, "/chat"),
      },

      "/dashboard": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },

      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});