import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");

  return {
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      port: 5173,
      strictPort: true,
      // Bind mounts from Windows/macOS hosts don't emit file events inside the container.
      watch: { usePolling: env.VITE_USE_POLLING === "true" },
      proxy: {
        "/api": {
          target: env.API_PROXY_TARGET ?? "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
  };
});
