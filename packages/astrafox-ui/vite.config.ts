import { defineConfig } from "vite";
import { resolve } from "path";
import react from "@vitejs/plugin-react";
import vue from "@vitejs/plugin-vue";
import dts from "vite-plugin-dts";

export default defineConfig({
  plugins: [
    react({ jsxRuntime: "automatic" }),
    vue(),
    dts({
      insertTypesEntry: true,
      outDir: "dist",
      include: ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
    }),
  ],
  build: {
    lib: {
      entry: {
        index: resolve(__dirname, "src/index.ts"),
        "react/index": resolve(__dirname, "src/react/index.ts"),
        "vue/index": resolve(__dirname, "src/vue/index.ts"),
        "core/config": resolve(__dirname, "src/core/config.ts"),
        "core/themes": resolve(__dirname, "src/core/themes.ts"),
      },
      formats: ["es"],
    },
    rollupOptions: {
      external: ["react", "react-dom", "react/jsx-runtime", "vue"],
      output: {
        preserveModules: false,
        entryFileNames: "[name].js",
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
          "react/jsx-runtime": "jsxRuntime",
          vue: "Vue",
        },
      },
    },
    outDir: "dist",
    sourcemap: true,
    minify: "esbuild",
  },
});
