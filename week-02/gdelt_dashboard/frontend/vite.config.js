import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  // третий аргумент "" - загружаем все переменные из .env, не только с префиксом VITE_
  const env = loadEnv(mode, process.cwd(), "");
  const frontendPort = Number(env.FRONTEND_PORT) || 5173;
  const backendPort = Number(env.BACKEND_PORT) || 8000;

  return {
    plugins: [react()],
    server: {
      port: frontendPort,
      proxy: {
        "/api": {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  };
});
