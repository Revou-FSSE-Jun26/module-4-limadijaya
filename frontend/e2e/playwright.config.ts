import { defineConfig } from "@playwright/test";

// Playwright skeleton (T1.06). The target environment and the E2E account are not
// decided yet (UD-16, UD-22), so nothing here names a URL or an environment.
// The base URL must be supplied through PLAYWRIGHT_BASE_URL, and the run fails
// clearly when it is missing (TEST-006-AC01).
const baseURL = process.env.PLAYWRIGHT_BASE_URL;

if (!baseURL) {
  throw new Error("PLAYWRIGHT_BASE_URL is not set. Set it to the URL of the frontend under test.");
}

export default defineConfig({
  testDir: ".",
  testMatch: "**/*.spec.ts",
  use: {
    baseURL,
  },
});
