import { expect, test } from "@playwright/test";
import { addCard, addColumn, createBoardAndOpen, logIn, registerUser, uniqueEmail } from "./helpers";

test("complete Kanban board journey", async ({ page, browser, request, baseURL }) => {
  const ownerEmail = uniqueEmail("owner");
  const teammateEmail = uniqueEmail("mate");
  const boardName = `E2E board ${Date.now()}`;
  await registerUser(request, baseURL as string, "Olivia Owner", ownerEmail);
  await registerUser(request, baseURL as string, "Tariq Teammate", teammateEmail);

  await test.step("1. Log in", async () => {
    await logIn(page, ownerEmail);
  });

  await test.step("2. Create a board and open it", async () => {
    await createBoardAndOpen(page, boardName);
  });

  await test.step("3. Add columns", async () => {
    await addColumn(page, "To do");
    await addColumn(page, "Doing");
    await expect(page.getByTestId("column")).toHaveCount(2);
  });

  await test.step("4. Create cards", async () => {
    await addCard(page, "To do", "Write spec");
    await addCard(page, "To do", "Review PR");
  });

  await test.step("5. Drag a card to another column and keep it after a reload", async () => {
    const todo = page.getByRole("region", { name: "Column To do" });
    const doing = page.getByRole("region", { name: "Column Doing" });
    await todo.getByTestId("card").filter({ hasText: "Write spec" }).dragTo(doing.getByTestId("column-dropzone"), {
      sourcePosition: { x: 6, y: 6 },
    });
    await expect(doing.getByTestId("card").filter({ hasText: "Write spec" })).toBeVisible();
    await page.reload();
    await expect(
      page.getByRole("region", { name: "Column Doing" }).getByTestId("card").filter({ hasText: "Write spec" }),
    ).toBeVisible();
    await expect(
      page.getByRole("region", { name: "Column To do" }).getByTestId("card").filter({ hasText: "Write spec" }),
    ).toHaveCount(0);
  });

  await test.step("6. Add and edit a comment", async () => {
    await page.getByRole("button", { name: "Open card Write spec" }).click();
    const dialog = page.getByRole("dialog", { name: "Card details" });
    await dialog.getByLabel("Add a comment").fill("First draft is ready");
    await dialog.getByRole("button", { name: "Post comment" }).click();
    await expect(dialog.getByTestId("comment")).toContainText("First draft is ready");
    await dialog.getByRole("button", { name: "Edit" }).click();
    await dialog.getByLabel("Edit comment").fill("Second draft is ready");
    await dialog.getByRole("button", { name: "Save comment" }).click();
    await expect(dialog.getByTestId("comment")).toContainText("Second draft is ready");
    await expect(dialog.getByTestId("comment")).toContainText("edited");
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
  });

  await test.step("7. Search for a card with the debounced filter", async () => {
    await page.getByLabel("Search cards").fill("review");
    await expect(page.getByTestId("card").filter({ hasText: "Review PR" })).toBeVisible();
    await expect(page.getByTestId("card").filter({ hasText: "Write spec" })).toBeHidden();
    await page.getByLabel("Search cards").fill("");
    await expect(page.getByTestId("card").filter({ hasText: "Write spec" })).toBeVisible();
  });

  await test.step("8. Assign a teammate and see the unread count on their notification bell", async () => {
    await page.getByRole("button", { name: "Add member" }).click();
    await page.getByLabel("Member email").fill(teammateEmail);
    await page.getByRole("button", { name: "Add member" }).last().click();
    await expect(page.getByText("Members: Olivia Owner, Tariq Teammate")).toBeVisible();

    await page.getByRole("button", { name: "Open card Write spec" }).click();
    const dialog = page.getByRole("dialog", { name: "Card details" });
    await dialog.getByLabel("Assignee").selectOption({ label: "Tariq Teammate" });
    await expect(dialog.getByLabel("Assignee")).toHaveValue(/.+/);
    await page.keyboard.press("Escape");

    const teammateContext = await browser.newContext();
    const teammatePage = await teammateContext.newPage();
    await logIn(teammatePage, teammateEmail);
    await expect(teammatePage.getByRole("button", { name: "Notifications, 1 unread" })).toBeVisible();
    await teammatePage.getByRole("link", { name: "My Tasks" }).click();
    await expect(teammatePage.getByRole("link", { name: "Write spec" })).toBeVisible();
    await teammateContext.close();
  });
});