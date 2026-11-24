import { expect, test } from "@playwright/test";
import { PASSWORD, logIn, registerUser, uniqueEmail } from "./helpers";

test.describe("authentication flows", () => {
  let email: string;

  test.beforeAll(async ({ request, baseURL }) => {
    email = uniqueEmail("auth");
    await registerUser(request, baseURL as string, "Auth Tester", email);
  });

  test("successful login redirects to the dashboard", async ({ page }) => {
    await logIn(page, email);
    await expect(page).toHaveURL("/");
    await expect(page.getByRole("navigation", { name: "Main" })).toBeVisible();
  });

  test("invalid credentials show an error and stay on /login", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(`${PASSWORD}-wrong`);
    await page.getByRole("button", { name: "Log in" }).click();
    await expect(page.getByRole("alert").filter({ hasText: "Invalid email or password." })).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);
  });

  test("an unauthenticated visitor is redirected to /login", async ({ page }) => {
    for (const path of ["/", "/my-tasks", "/profile"]) {
      await page.goto(path);
      await expect(page).toHaveURL(/\/login$/);
    }
  });

  test("logging out redirects to /login and protects the pages again", async ({ page }) => {
    await logIn(page, email);
    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login$/);
    await page.goto("/");
    await expect(page).toHaveURL(/\/login$/);
  });
});