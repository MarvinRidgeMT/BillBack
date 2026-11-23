import { expect, test } from "@playwright/test";

const eligibility = {
  status: "likely_free",
  tier: null,
  evidence: { quote: "Free care up to 200% FPG.", page: 3, confidence: 0.98, verified: true, status: "stated" },
  caveats: [],
  disclaimer: "Likely eligible — not a guarantee",
  percent_of_fpl: 150,
  hospital_name: "Adena Health System",
  source_url: null,
  engine: "test",
  fpl_year: 2026,
};

test("navigator cases stay in memory and download one ZIP", async ({ page }) => {
  await page.route("**/api/hospitals", (route) => route.fulfill({ json: { success: true, data: [{ slug: "adena-health-system", name: "Adena Health System", state: "OH" }], error: null } }));
  await page.route("**/api/hospitals/match", (route) => route.fulfill({ json: { success: true, data: { slug: "adena-health-system", matched: true }, error: null } }));
  await page.route("**/api/eligibility", (route) => route.fulfill({ json: { success: true, data: eligibility, error: null } }));
  await page.route("**/api/eob/compare", (route) => route.fulfill({ json: { success: true, data: { matched_claim_index: 0, match_score: 100, discrepancies: [] }, error: null } }));
  await page.route("**/api/policy/facts?*", (route) => route.fulfill({ json: { success: true, data: {
    hospital_name: "Adena Health System", hospital_state: "OH", state_law: null,
    application_window: { days: 240, counted_from: "first_post_discharge_billing_statement", quote: "", page: null },
    presumptive_eligibility: null, has_page_images: false, source_url: null,
  }, error: null } }));
  await page.route("**/api/packet", (route) => route.fulfill({ status: 200, contentType: "application/pdf", body: "%PDF-1.4\n%%EOF" }));
  await page.route("**/api/schedule-h/**", (route) => route.fulfill({ status: 404, json: { detail: "not matched" } }));
  await page.route("**/api/policy/**", (route) => route.fulfill({ status: 404, json: { detail: "not in test" } }));

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.getByLabel("I'm helping someone else").check();
  await expect(page.getByText(/Cases stay only in this tab/i)).toBeVisible();
  await page.getByRole("button", { name: /check my bill/i }).click();
  await expect(page.getByRole("heading", { name: "Add the person's hospital bill" })).toBeVisible();
  await page.getByRole("button", { name: "Try a sample with insurance", exact: true }).click();
  await page.getByRole("button", { name: "It's right" }).click();
  await page.getByRole("button", { name: "Looks right" }).click();
  await page.getByRole("button", { name: "Compare bill and insurance" }).click();
  await expect(page.getByRole("heading", { name: "About the person you're helping" })).toBeVisible();
  await page.getByLabel("Yearly household income, before taxes").fill("20,000");
  await page.getByRole("button", { name: "See my result" }).click();

  await expect(page.getByRole("heading", { name: "They likely qualify for a $0 bill" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Cases in this tab" })).toBeVisible();
  await expect(page.getByText("Result ready")).toBeVisible();
  await expect(page.getByRole("button", { name: /Print one-page summary/ })).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download everything" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("BillBack-navigator-cases.zip");
  await expect(page.getByText("Packet downloaded")).toBeVisible();
});
