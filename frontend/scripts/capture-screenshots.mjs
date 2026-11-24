// Captures the README screenshots against any running RevoTask frontend.
//   PLAYWRIGHT_BASE_URL=https://your-app.vercel.app node scripts/capture-screenshots.mjs [outputDir]
// It registers two throwaway users through the public register endpoint, so it needs no secrets.
import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL;
if (!baseURL) throw new Error("PLAYWRIGHT_BASE_URL is not set.");
const outDir = process.argv[2] ?? "../evidence/screenshots";
mkdirSync(outDir, { recursive: true });
const shot = (page, name, options = {}) => page.screenshot({ path: join(outDir, `${name}.png`), ...options });

const password = "Passw0rd-shots";
const stamp = Date.now();
const owner = { name: "Olivia Owner", email: `owner-${stamp}@example.com` };
const mate = { name: "Tariq Teammate", email: `mate-${stamp}@example.com` };

const browser = await chromium.launch();
const context = await browser.newContext({ baseURL, viewport: { width: 1280, height: 800 } });
const page = await context.newPage();

for (const user of [owner, mate]) {
  const response = await context.request.post("/api/auth/register", {
    headers: { Origin: new URL(baseURL).origin },
    data: { ...user, password },
  });
  if (response.status() !== 201) throw new Error(`register failed: ${response.status()}`);
}

// Public pages.
await page.goto("/register");
await shot(page, "register");
await page.goto("/login");
await shot(page, "login");
await page.getByLabel("Email").fill(owner.email);
await page.getByLabel("Password").fill(password);
await page.getByRole("button", { name: "Log in" }).click();
await page.getByRole("heading", { name: "Your boards" }).waitFor();

// Board with columns and cards.
await page.getByLabel("Board name").fill("Website redesign");
await page.getByRole("button", { name: "Create board" }).click();
await page.getByRole("link", { name: "Website redesign" }).waitFor();
await shot(page, "dashboard", { fullPage: true });
await page.getByRole("link", { name: "Website redesign" }).click();
await page.getByRole("heading", { name: "Website redesign" }).waitFor();

for (const name of ["To do", "Doing", "Done"]) {
  await page.getByLabel("New column name").fill(name);
  await page.getByRole("button", { name: "Add column" }).click();
  await page.getByRole("region", { name: `Column ${name}` }).waitFor();
}
const addCard = async (column, title) => {
  const region = page.getByRole("region", { name: `Column ${column}` });
  await region.getByLabel(`New card title in ${column}`).fill(title);
  await region.getByRole("button", { name: "Add card" }).click();
  await region.getByTestId("card").filter({ hasText: title }).waitFor();
};
await addCard("To do", "Write the brief");
await addCard("To do", "Design the homepage");
await addCard("Doing", "Set up the repository");
await shot(page, "board-detail", { fullPage: true });

// A card being dragged: hold the mouse over another column so the drop target is highlighted.
const card = page.getByRole("region", { name: "Column To do" }).getByTestId("card").filter({ hasText: "Write the brief" });
const target = page.getByRole("region", { name: "Column Doing" }).getByTestId("column-dropzone");
const cardBox = await card.boundingBox();
const targetBox = await target.boundingBox();
await page.mouse.move(cardBox.x + 6, cardBox.y + 6);
await page.mouse.down();
await page.mouse.move(cardBox.x + 40, cardBox.y + 20, { steps: 5 });
await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2, { steps: 15 });
await shot(page, "card-dragging");
await page.mouse.up();
await page.getByRole("region", { name: "Column Doing" }).getByTestId("card").filter({ hasText: "Write the brief" }).waitFor();
await shot(page, "card-after-drop", { fullPage: true });

// Card detail modal with a comment, plus assignment for the notification.
await page.getByRole("button", { name: "Add member" }).click();
await page.getByLabel("Member email").fill(mate.email);
await page.getByRole("button", { name: "Add member" }).last().click();
await page.getByText(`Members: ${owner.name}, ${mate.name}`).waitFor();
await page.getByRole("button", { name: "Open card Write the brief" }).click();
const dialog = page.getByRole("dialog", { name: "Card details" });
await dialog.getByLabel("Assignee").selectOption({ label: mate.name });
await dialog.getByLabel("Add a comment").fill("The first draft is ready for review.");
await dialog.getByRole("button", { name: "Post comment" }).click();
await dialog.getByTestId("comment").waitFor();
await shot(page, "card-detail-modal");
await page.keyboard.press("Escape");
await page.getByLabel("Search cards").fill("homepage");
await page.getByTestId("card").filter({ hasText: "Write the brief" }).waitFor({ state: "hidden" });
await shot(page, "card-search");

// Teammate: notification bell with an unread count, My Tasks, Profile.
const mateContext = await browser.newContext({ baseURL, viewport: { width: 1280, height: 800 } });
const matePage = await mateContext.newPage();
await matePage.goto("/login");
await matePage.getByLabel("Email").fill(mate.email);
await matePage.getByLabel("Password").fill(password);
await matePage.getByRole("button", { name: "Log in" }).click();
await matePage.getByRole("button", { name: /Notifications, [1-9]\d* unread/ }).waitFor();
await matePage.getByRole("button", { name: /Notifications, [1-9]\d* unread/ }).click();
await matePage.getByText("assigned you to").waitFor();
await shot(matePage, "notification-bell");
await matePage.keyboard.press("Escape");
await matePage.goto("/my-tasks");
await matePage.getByRole("heading", { name: "My Tasks" }).waitFor();
await shot(matePage, "my-tasks");
await matePage.goto("/profile");
await matePage.getByRole("heading", { name: "Your profile" }).waitFor();
await shot(matePage, "profile");
await mateContext.close();

// Mobile (360 px) screenshots.
const mobile = await browser.newContext({ baseURL, viewport: { width: 360, height: 740 }, hasTouch: true });
const mobilePage = await mobile.newPage();
await mobilePage.goto("/login");
await mobilePage.getByLabel("Email").fill(owner.email);
await mobilePage.getByLabel("Password").fill(password);
await mobilePage.getByRole("button", { name: "Log in" }).click();
await mobilePage.getByRole("heading", { name: "Your boards" }).waitFor();
await shot(mobilePage, "mobile-dashboard", { fullPage: true });
await mobilePage.getByRole("link", { name: "Website redesign" }).click();
await mobilePage.getByRole("heading", { name: "Website redesign" }).waitFor();
await shot(mobilePage, "mobile-board", { fullPage: true });
await mobile.close();

await browser.close();
console.log(`Screenshots written to ${outDir}`);
