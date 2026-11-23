import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const eligibility = {
  status: "likely_free",
  tier: null,
  evidence: {
    quote: "Patients at or below 200% of the Federal Poverty Guidelines are eligible for a full discount.",
    page: 3,
    confidence: 0.98,
    verified: true,
    status: "stated",
  },
  caveats: [],
  disclaimer: "Likely eligible — not a guarantee",
  percent_of_fpl: 150,
  hospital_name: "USA Health",
  source_url: null,
  engine: "test",
  fpl_year: 2026,
};

async function mockApi(page: Page) {
  await page.route("**/api/hospitals", (route) =>
    route.fulfill({ json: { success: true, data: [{ slug: "usa-health", name: "USA Health", state: "AL" }], error: null } }),
  );
  await page.route("**/api/hospitals/match", (route) =>
    route.fulfill({ json: { success: true, data: { slug: "usa-health", matched: true }, error: null } }),
  );
  await page.route("**/api/config", (route) =>
    route.fulfill({ json: { success: true, data: { live_mode: false }, error: null } }),
  );
  await page.route("**/api/eligibility", (route) =>
    route.fulfill({ json: { success: true, data: eligibility, error: null } }),
  );
  await page.route("**/api/eob/compare", (route) =>
    route.fulfill({ json: { success: true, data: { matched_claim_index: 0, match_score: 100, discrepancies: [] }, error: null } }),
  );
  await page.route("**/api/policy/**", (route) =>
    route.fulfill({ status: 404, json: { detail: "not in accessibility fixture" } }),
  );
}

async function audit(page: Page, label: string) {
  // Let AnimatePresence finish so axe does not measure blended exit-state colors.
  await page.waitForTimeout(700);
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter((item) => item.impact === "serious" || item.impact === "critical");
  const ids = results.violations.map((item) => `${item.id}:${item.impact ?? "unknown"}`).join(", ") || "none";
  console.log(`AXE ${label}: ${results.violations.length} total, ${serious.length} serious/critical (${ids})`);
  expect(serious, `${label}: ${serious.map((item) => item.id).join(", ")}`).toEqual([]);
}

async function auditEnglishAndSpanish(page: Page, label: string) {
  await audit(page, `${label} EN`);
  await page.getByRole("combobox", { name: "Language" }).selectOption("es");
  await expect(page.locator("html")).toHaveAttribute("lang", "es");
  await audit(page, `${label} ES`);
  await page.getByRole("combobox", { name: "Idioma" }).selectOption("en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
}

test("every patient step has no serious or critical axe violations in EN/ES", async ({ page }) => {
  await mockApi(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await auditEnglishAndSpanish(page, "hero");

  await page.getByRole("button", { name: /check my bill/i }).click();
  await auditEnglishAndSpanish(page, "upload");

  await page.getByRole("button", { name: "Try a sample with insurance" }).click();
  await expect(page.getByRole("heading", { name: "Check what we found" })).toBeVisible();
  await auditEnglishAndSpanish(page, "bill confirmation");
  await page.getByRole("button", { name: "It's right" }).click();
  await page.getByRole("button", { name: "Looks right" }).click();

  await expect(page.getByRole("heading", { name: "Check the insurance details" })).toBeVisible();
  await auditEnglishAndSpanish(page, "insurance confirmation");
  await page.getByRole("button", { name: "Compare bill and insurance" }).click();

  await expect(page.getByRole("heading", { name: "Two quick questions" })).toBeVisible();
  await auditEnglishAndSpanish(page, "questions");
  await page.getByLabel("Yearly household income, before taxes").fill("20,000");
  await page.getByRole("button", { name: "See my result" }).click();

  await expect(page.getByRole("heading", { name: "Likely free care" })).toBeVisible();
  await auditEnglishAndSpanish(page, "result");
});

test("easy-read mode holds at 200% zoom and keyboard focus reaches every control", async ({ page }) => {
  await mockApi(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.getByRole("button", { name: "Easy read" }).click();
  await expect(page.locator("html")).toHaveClass(/easy-read/);
  await page.evaluate(() => {
    document.body.style.zoom = "2";
  });
  await expect(page.locator("body")).toHaveCSS("overflow-x", "clip");
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus-visible")).toBeVisible();
  await audit(page, "easy read at 200% zoom");
});
