import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // The test targets are pure TypeScript utilities with no DOM, so the fast
    // default node environment is all that's needed. Only run our own src
    // tests, never anything under node_modules.
    include: ["src/**/*.test.ts"],
    environment: "node",
  },
});
