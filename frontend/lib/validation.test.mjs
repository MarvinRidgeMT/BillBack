// Run: node --test frontend/lib/validation.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import {
  checkHousehold,
  checkIncome,
  checkLimit,
  checkPolicyFile,
  checkPolicyUrl,
  checkState,
  stateFromAddress,
} from "./validation.ts";

test("household: 1-20, with a reason for each failure", () => {
  assert.deepEqual(checkHousehold("3"), { ok: true, value: 3 });
  assert.deepEqual(checkHousehold(" 20 "), { ok: true, value: 20 });
  assert.deepEqual(checkHousehold(""), { ok: false, error: "blank" });
  assert.deepEqual(checkHousehold("abc"), { ok: false, error: "blank" });
  assert.deepEqual(checkHousehold("0"), { ok: false, error: "zero" });
  assert.deepEqual(checkHousehold("21"), { ok: false, error: "too_many" });
  assert.deepEqual(checkHousehold("2.5"), { ok: false, error: "blank" });
});

test("income: blank and negative are errors, 0 is fine", () => {
  assert.deepEqual(checkIncome("41,000"), { ok: true, value: 41000 });
  assert.deepEqual(checkIncome("0"), { ok: true, value: 0 });
  assert.deepEqual(checkIncome(""), { ok: false, error: "blank" });
  assert.deepEqual(checkIncome("-"), { ok: false, error: "negative" });
  assert.deepEqual(checkIncome("-5,000"), { ok: false, error: "negative" });
  assert.deepEqual(checkIncome("10,000,001"), { ok: false, error: "too_high" });
});

test("limits: 100-600 percent, optional discount must be at least the free limit", () => {
  assert.deepEqual(checkLimit("200"), { ok: true, value: 200 });
  assert.deepEqual(checkLimit("250%"), { ok: true, value: 250 });
  assert.deepEqual(checkLimit(""), { ok: false, error: "blank" });
  assert.deepEqual(checkLimit("", { optional: true }), { ok: true, value: null });
  assert.deepEqual(checkLimit("99"), { ok: false, error: "out_of_range" });
  assert.deepEqual(checkLimit("601"), { ok: false, error: "out_of_range" });
  assert.deepEqual(checkLimit("lots"), { ok: false, error: "out_of_range" });
  assert.deepEqual(checkLimit("150", { optional: true, atLeast: 200 }), { ok: false, error: "below_free" });
  assert.deepEqual(checkLimit("400", { optional: true, atLeast: 200 }), { ok: true, value: 400 });
});

test("state codes and states in addresses", () => {
  assert.equal(checkState("wi"), "WI");
  assert.equal(checkState("Wisconsin"), null);
  assert.equal(stateFromAddress("100 Main St, Mobile, AL 36604"), "AL");
  assert.equal(stateFromAddress("611 E Sherman Ave, Fort Atkinson, WI 53538-1998"), "WI");
  assert.equal(stateFromAddress("Somewhere, OH"), "OH");
  assert.equal(stateFromAddress("no state here"), null);
  assert.equal(stateFromAddress(null), null);
});

test("policy links: http(s) only, scheme added when missing", () => {
  assert.deepEqual(checkPolicyUrl("https://example.org/fap.pdf"), { ok: true, value: "https://example.org/fap.pdf" });
  assert.deepEqual(checkPolicyUrl("example.org/fap"), { ok: true, value: "https://example.org/fap" });
  assert.deepEqual(checkPolicyUrl(""), { ok: false, error: "blank" });
  assert.deepEqual(checkPolicyUrl("javascript:alert(1)"), { ok: false, error: "not_web" });
  assert.deepEqual(checkPolicyUrl("ftp://example.org/x.pdf"), { ok: false, error: "not_web" });
  assert.deepEqual(checkPolicyUrl("not a link"), { ok: false, error: "not_web" });
});

test("policy files: PDFs up to 25 MB", () => {
  assert.equal(checkPolicyFile({ name: "fap.pdf", type: "application/pdf", size: 1000 }), "ok");
  assert.equal(checkPolicyFile({ name: "FAP.PDF", type: "", size: 1000 }), "ok");
  assert.equal(checkPolicyFile({ name: "bill.jpg", type: "image/jpeg", size: 1000 }), "not_pdf");
  assert.equal(checkPolicyFile({ name: "empty.pdf", type: "application/pdf", size: 0 }), "not_pdf");
  assert.equal(checkPolicyFile({ name: "big.pdf", type: "application/pdf", size: 26 * 1024 * 1024 }), "too_large");
});
