import { test, expect } from "@playwright/test";

test.describe("authentication journeys", () => {
  test("registration page is reachable", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: "Create your account" })).toBeVisible();
  });

  test("login page is reachable", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Log in" })).toBeVisible();
  });

  test("unauthenticated dashboard offers authentication", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "Register" })).toBeVisible();
  });
});
