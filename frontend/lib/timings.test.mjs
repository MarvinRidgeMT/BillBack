// Run: node --test frontend/lib/timings.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import { averages, getTimings, recordBillRead, recordTiming, resetTimings, subscribeTimings } from "./timings.ts";

test("records seconds and ignores bad numbers", () => {
  resetTimings();
  recordTiming("bill_read_s", 2.5);
  recordTiming("packet_s", "0.120");
  recordTiming("rules_s", "abc");
  recordTiming("rules_s", -1);
  recordTiming("rules_s", undefined);
  assert.deepEqual(getTimings().entries, [
    { key: "bill_read_s", seconds: 2.5 },
    { key: "packet_s", seconds: 0.12 },
  ]);
});

test("counts bills and low-confidence fields, never values", () => {
  resetTimings();
  recordBillRead([0.99, 0.71, 0.8, 0.5, 0.95]);
  recordBillRead([0.3]);
  const s = getTimings();
  assert.equal(s.bills, 2);
  assert.equal(s.lowConfidence, 3);
  assert.equal(s.fields, 6);
});

test("snapshots are new objects on change, so React re-renders", () => {
  resetTimings();
  const before = getTimings();
  let calls = 0;
  const off = subscribeTimings(() => calls++);
  recordTiming("rules_s", 0.01);
  off();
  recordTiming("rules_s", 0.02);
  assert.notEqual(getTimings(), before);
  assert.equal(calls, 1);
});

test("averages per step", () => {
  const avg = averages([
    { key: "rules_s", seconds: 1 },
    { key: "rules_s", seconds: 3 },
    { key: "packet_s", seconds: 0.5 },
  ]);
  assert.deepEqual(avg, { rules_s: { avg: 2, n: 2 }, packet_s: { avg: 0.5, n: 1 } });
});
