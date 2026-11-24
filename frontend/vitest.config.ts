import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Unit and component tests (FE-20). No coverage threshold is set, because UD-15 is open.
export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      // `server-only` throws outside the Next.js server build, so tests use an empty stub.
      "server-only": fileURLToPath(new URL("./tests/stubs/server-only.ts", import.meta.url)),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});