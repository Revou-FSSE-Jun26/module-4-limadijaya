import { expect, type APIRequestContext, type Page } from "@playwright/test";

/** The E2E account is created by each test run through the public register endpoint (UD-22 option: tests create their own users). */
export const PASSWORD = process.env.E2E_PASSWORD ?? "Passw0rd-e2e";

export function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

export async function registerUser(request: APIRequestContext, baseURL: string, name: string, email: string): Promise<void> {
  const response = await request.post(`${baseURL}/api/auth/register`, {
    headers: { Origin: new URL(baseURL).origin },
    data: { name, email, password: PASSWORD },
  });
  expect(response.status(), "register response").toBe(201);
}

export async function logIn(page: Page, email: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("heading", { name: "Your boards" })).toBeVisible();
}

export async function createBoardAndOpen(page: Page, name: string): Promise<void> {
  await page.getByLabel("Board name").fill(name);
  await page.getByRole("button", { name: "Create board" }).click();
  await page.getByRole("link", { name }).click();
  await expect(page.getByRole("heading", { name })).toBeVisible();
}

export async function addColumn(page: Page, name: string): Promise<void> {
  await page.getByLabel("New column name").fill(name);
  await page.getByRole("button", { name: "Add column" }).click();
  await expect(page.getByRole("region", { name: `Column ${name}` })).toBeVisible();
}

export async function addCard(page: Page, columnName: string, title: string): Promise<void> {
  const column = page.getByRole("region", { name: `Column ${columnName}` });
  await column.getByLabel(`New card title in ${columnName}`).fill(title);
  await column.getByRole("button", { name: "Add card" }).click();
  await expect(column.getByTestId("card").filter({ hasText: title })).toBeVisible();
}