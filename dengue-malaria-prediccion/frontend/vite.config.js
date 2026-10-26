import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// En desarrollo, /api/* se reenvia a la API local (sin CORS); en Docker lo hace nginx.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/preparar.js"],
    css: false,
  },
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
