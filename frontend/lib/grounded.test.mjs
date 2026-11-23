// Run: node --test frontend/lib/grounded.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import { describeGrounded, fieldsToCheck, PROBLEM_CODES, problemKey, problemKeys } from "./grounded.ts";
import en from "../messages/en.json" with { type: "json" };
import es from "../messages/es.json" with { type: "json" };

test("every problem code maps to a message in both languages", () => {
  for (const code of PROBLEM_CODES) {
    const key = problemKey(code);
    assert.equal(key, `problem.${code}`);
    assert.ok(en[key] && es[key], key);
  }
  assert.equal(problemKey("something_new"), "problem.other");
  assert.ok(en["problem.other"] && es["problem.other"]);
});

test("problem lists are de-duplicated, unknown codes folded", () => {
  assert.deepEqual(problemKeys(["low_confidence", "x", "y", "low_confidence"]), ["problem.low_confidence", "problem.other"]);
  assert.deepEqual(problemKeys([]), []);
});

test("grounded values in plain words", () => {
  assert.deepEqual(describeGrounded("free_care", 200), { key: "live.value.free_up_to", vars: { pct: 200 } });
  assert.deepEqual(describeGrounded("free_care", null), { key: "live.value.not_stated" });
  assert.deepEqual(describeGrounded("discount", { fpl_max_percent: 400, tiers: [] }), {
    key: "live.value.discount_up_to",
    vars: { pct: 400 },
  });
  assert.deepEqual(describeGrounded("discount", { fpl_max_percent: null, tiers: [{}, {}] }), {
    key: "live.value.discount_tiers",
    vars: { n: 2 },
  });
  assert.deepEqual(describeGrounded("asset_test", { applies: false, details: null }), { key: "live.value.assets_dont_count" });
  assert.deepEqual(describeGrounded("asset_test", { applies: null }), { key: "live.value.not_stated" });
  assert.deepEqual(describeGrounded("residency", { required: true, area: "Dane County" }), {
    key: "live.value.residency_area",
    vars: { area: "Dane County" },
  });
  assert.deepEqual(describeGrounded("residency", { required: true, area: null }), { key: "live.value.residency_required" });
  assert.deepEqual(describeGrounded("application_window", { days: 240, counted_from: "date_of_service" }), {
    key: "live.value.window_from_service",
    vars: { days: 240 },
  });
  assert.deepEqual(describeGrounded("application_window", { days: 240, counted_from: "other" }), {
    key: "live.value.window_days",
    vars: { days: 240 },
  });
  assert.deepEqual(describeGrounded("application_window", { days: null }), { key: "live.value.not_stated" });
  // Mad River (live check, 2026-11-23): "MRCH will not impose an application deadline" is stated, with no number.
  assert.deepEqual(describeGrounded("application_window", { days: null }, "stated"), { key: "live.value.window_no_number" });
});

test("every value key has both languages", () => {
  const samples = [
    describeGrounded("free_care", 1),
    describeGrounded("free_care", null),
    describeGrounded("discount", { fpl_max_percent: 1 }),
    describeGrounded("discount", { tiers: [1] }),
    describeGrounded("asset_test", { applies: true }),
    describeGrounded("asset_test", { applies: false }),
    describeGrounded("residency", { required: true, area: "x" }),
    describeGrounded("residency", { required: true }),
    describeGrounded("residency", { required: false }),
    describeGrounded("application_window", { days: 1 }),
    describeGrounded("application_window", { days: 1, counted_from: "date_of_service" }),
    describeGrounded("application_window", { days: 1, counted_from: "discharge" }),
    describeGrounded("application_window", { days: 1, counted_from: "first_post_discharge_billing_statement" }),
  ];
  for (const { key } of samples) assert.ok(en[key] && es[key], key);
});

test("bill fields to check: under 80% or flagged by the backend", () => {
  const names = ["a", "b", "c", "d"];
  const fields = { a: { confidence: 0.95 }, b: { confidence: 0.79 }, c: { confidence: 0.9 }, d: { confidence: NaN } };
  assert.deepEqual(fieldsToCheck(names, fields), ["b", "d"]);
  assert.deepEqual(fieldsToCheck(names, fields, ["c"]), ["b", "c", "d"]);
  assert.deepEqual(fieldsToCheck(names, { a: { confidence: 0.8 }, b: { confidence: 1 }, c: { confidence: 1 }, d: { confidence: 1 } }), []);
});
