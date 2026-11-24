import { defineConfig, devices } from "@playwright/test";

// Playwright runs against a deployed or local frontend. The base URL always comes from
// PLAYWRIGHT_BASE_URL, and the run fails clearly when it is missing (TEST-006-AC01, FE-21).
const baseURL = process.env.PLAYWRIGHT_BASE_URL;
if (!baseURL) {
  throw new Error("PLAYWRIGHT_BASE_URL is not set. Set it to the URL of the frontend under test.");
}

export default defineConfig({
  testDir: ".",
  testMatch: "**/*.spec.ts",
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ["list"],
    ["html", { outputFolder: "../../evidence/playwright-report", open: "never" }],
  ],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    actionTimeout: 15_000,
    navigationTimeout: 45_000,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});