import { resolve } from "node:path";

import { defineConfig } from "vitest/config";

// P1 тесты — чистый TS (контракт событий, хелперы), без рендера React,
// поэтому plugin-react не нужен. Компонентные тесты добавятся в P7 вместе с UI.
export default defineConfig({
  resolve: {
    alias: { "@": resolve(__dirname, ".") },
  },
  test: {
    environment: "node",
    include: ["lib/**/*.test.ts", "lib/**/*.test.tsx"],
    coverage: {
      provider: "v8",
      include: ["lib/**/*.ts"],
      exclude: ["lib/**/*.test.ts"],
      thresholds: { lines: 70, functions: 70, statements: 70 },
      reporter: ["text", "json"],
    },
  },
});
