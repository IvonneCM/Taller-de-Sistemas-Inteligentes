import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo, /api/* se reenvia a la API local (sin CORS); en Docker lo hace nginx.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
