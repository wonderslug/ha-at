import { defineConfig } from "vitest/config";

// One ES module with Lit bundled in, committed so HACS installs in one step.
export default defineConfig({
  build: {
    lib: {
      entry: "src/at-panel.ts",
      formats: ["es"],
      fileName: () => "at-panel.js",
    },
    outDir: "../custom_components/at/frontend",
    emptyOutDir: true,
    minify: true,
    target: "es2022",
    rollupOptions: { output: { inlineDynamicImports: true } },
  },
  test: {
    include: ["test/**/*.test.ts"],
    environment: "node",
  },
});
