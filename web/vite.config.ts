import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages project site: https://<user>.github.io/<repo>/
const REPO_NAME = "BAGZINE";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === "production" ? `/${REPO_NAME}/` : "/",
  server: {
    port: 5173,
  },
}));
