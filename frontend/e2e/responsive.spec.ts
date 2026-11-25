import { expect, test, type Page } from "@playwright/test";
import { addCard, addColumn, createBoardAndOpen, logIn, registerUser, uniqueEmail } from "./helpers";

test.use({ viewport: { width: 360, height: 740 }, hasTouch: true });

async function hasNoHorizontalPageScroll(page: Page): Promise<boolean> {
  return page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth);
}

test("usable at 360 px with a non-drag way to move a card (DA-18)", async ({ page, request, baseURL }) => {
  const email = uniqueEmail("mobile");
  await registerUser(request, baseURL as string, "Mobile Tester", email);

  await page.goto("/login");
  expect(await hasNoHorizontalPageScroll(page)).toBe(true);
  await page.goto("/register");
  expect(await hasNoHorizontalPageScroll(page)).toBe(true);

  await logIn(page, email);
  expect(await hasNoHorizontalPageScroll(page)).toBe(true);

  await createBoardAndOpen(page, `Mobile board ${Date.now()}`);
  await addColumn(page, "To do");
  await addColumn(page, "Done soon");
  await addColumn(page, "Third column");
  await addColumn(page, "Fourth column");
  await addCard(page, "To do", "Tap to move");
  expect(await hasNoHorizontalPageScroll(page)).toBe(true);

  await page.getByRole("button", { name: "Move card Tap to move" }).tap();
  const dialog = page.getByRole("dialog", { name: "Move card: Tap to move" });
  await dialog.getByLabel("Column").selectOption({ label: "Done soon" });
  await dialog.getByRole("button", { name: "Move card" }).tap();
  await expect(
    page.getByRole("region", { name: "Column Done soon" }).getByTestId("card").filter({ hasText: "Tap to move" }),
  ).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: "Card moved to Done soon" })).toBeAttached();
});