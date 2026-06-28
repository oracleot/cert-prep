import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    include: ["app/__tests__/**/*.test.ts", "app/__tests__/**/*.test.tsx"],
    environment: "node",
    globals: false,
    coverage: {
      provider: "v8",
      include: ["app/agents/prompts/**/*.ts"],
      exclude: ["**/*.d.ts", "**/*.test.ts", "**/__tests__/**"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
});
