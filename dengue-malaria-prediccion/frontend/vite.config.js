import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// A donde reenvia el servidor de desarrollo las llamadas a /api/* (sin CORS,
// porque la peticion sale del servidor de Vite y no del navegador):
//   npm run dev         -> API local (http://localhost:8000 por defecto)
//   npm run dev:render  -> la URL de API_TARGET en frontend/.env.render
// API_TARGET tambien puede ir en .env.local o en el entorno del sistema.
// Ver frontend/.env.example. En Docker lo hace nginx (nginx.conf); en una
// compilacion de produccion se puede fijar la URL con VITE_API_URL.
const API_LOCAL_POR_DEFECTO = "http://localhost:8000";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const target = env.API_TARGET || (mode === "render" ? null : API_LOCAL_POR_DEFECTO);
  if (!target) {
    throw new Error(
      "Falta API_TARGET para el modo 'render'. Copie frontend/.env.example a " +
        "frontend/.env.render y complete la URL de la API.",
    );
  }

  return {
    plugins: [react()],
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/preparar.js"],
      css: false,
    },
    server: {
      proxy: {
        "/api": {
          target,
          // Render enruta por el encabezado Host: sin esto responde 404.
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
