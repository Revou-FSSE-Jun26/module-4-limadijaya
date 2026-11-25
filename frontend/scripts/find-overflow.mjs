// Finds elements that make the page wider than the viewport at 360 px.
//   PLAYWRIGHT_BASE_URL=... node scripts/find-overflow.mjs
import { chromium } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL;
if (!baseURL) throw new Error("PLAYWRIGHT_BASE_URL is not set.");
const email = `overflow-${Date.now()}@example.com`;
const password = "Passw0rd-shots";
const browser = await chromium.launch();
const context = await browser.newContext({ baseURL, viewport: { width: 360, height: 740 }, hasTouch: true });
const reg = await context.request.post("/api/auth/register", {
  headers: { Origin: new URL(baseURL).origin },
  data: { name: "Overflow Tester", email, password },
});
if (reg.status() !== 201) throw new Error(`register ${reg.status()}`);
const page = await context.newPage();
await page.goto("/login");
await page.getByLabel("Email").fill(email);
await page.getByLabel("Password").fill(password);
await page.getByRole("button", { name: "Log in" }).click();
await page.getByLabel("Board name").fill("Overflow board");
await page.getByRole("button", { name: "Create board" }).click();
await page.getByRole("link", { name: "Overflow board" }).click();
await page.waitForURL(/\/boards\//);
for (const name of ["To do", "Doing", "Done"]) {
  await page.getByLabel("New column name").fill(name);
  await page.getByRole("button", { name: "Add column" }).click();
  await page.getByRole("region", { name: `Column ${name}` }).waitFor();
}
const report = await page.evaluate(() => {
  const vw = document.documentElement.clientWidth;
  const out = { clientWidth: vw, scrollWidth: document.documentElement.scrollWidth, offenders: [] };
  for (const el of document.querySelectorAll("body *")) {
    if (el.closest('[data-testid="columns-scroller"]')) continue; // inside the intended scroll area
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1) out.offenders.push(`${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}.${String(el.className).slice(0, 70)} right=${Math.round(r.right)}`);
  }
  return out;
});
const chain = await page.evaluate(() => { const rows = []; let el = document.querySelector('[data-testid="columns-scroller"]'); while (el) { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); rows.push(`${el.tagName.toLowerCase()}.${String(el.className).slice(0,50)} w=${Math.round(r.width)} display=${cs.display} overflowX=${cs.overflowX} minW=${cs.minWidth}`); el = el.parentElement; } return rows; });
console.log(JSON.stringify(report, null, 1)); console.log(chain.join("\n"));
await browser.close();
