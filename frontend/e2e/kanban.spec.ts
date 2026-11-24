import { test, expect } from "@playwright/test";

test.describe("Kanban foundation", () => {
  test("dashboard loads without a fixed deployment URL", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "RevoTask" })).toBeVisible();
  });

  test("mobile layout remains readable", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "RevoTask" })).toBeVisible();
  });
});
