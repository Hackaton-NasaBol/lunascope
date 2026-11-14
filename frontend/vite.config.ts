import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";

// Cesium necesita servir sus Workers, Assets, ThirdParty y Widgets como archivos estáticos.
const cesiumSource = "node_modules/cesium/Build/Cesium";
const cesiumBaseUrl = "cesium";

export default defineConfig({
  define: {
    CESIUM_BASE_URL: JSON.stringify(`/${cesiumBaseUrl}`),
  },
  plugins: [
    react(),
    tailwindcss(),
    viteStaticCopy({
      targets: ["Workers", "ThirdParty", "Assets", "Widgets"].map((d) => ({
        src: `${cesiumSource}/${d}`,
        dest: cesiumBaseUrl,
        rename: { stripBase: 4 }, // quita node_modules/cesium/Build/Cesium → /cesium/Workers/...
      })),
    }),
  ],
  server: { port: 5173, strictPort: true },
});
